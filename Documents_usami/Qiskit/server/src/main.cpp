#include <Python.h>
#include <fmt/format.h>
#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include <grpcpp/grpcpp.h>
#include <quill/Backend.h>
#include <quill/Frontend.h>
#include <quill/LogMacros.h>
#include <quill/Logger.h>
#include <quill/sinks/ConsoleSink.h>
#include <boost/program_options.hpp>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <regex>
#include <string>
#include <thread>
#include "config.h"
#include "job_utils.h"
#include "server.h"
#include <csignal>


namespace grpc_qc_simulator
{
    std::atomic_int32_t LastFinishedJobId = -1;

    /**
     * @brief Starts a server and listens for incoming connections on the specified address and port.
     *
     * @param address Address to listen on.
     * @param port Port number to listen on.
     * @param job_results_dir Directory where job results are stored.
     * @param job_queue Job queue to use for managing jobs.
     * @param logger Logger to use for logging messages.
     */

    // TASKS : add TLS support
    void RunServer(std::string_view address, const std::uint16_t port, const std::filesystem::path& job_results_dir,
                   JobQueue& job_queue, quill::Logger* logger)
    {
        // https://github.com/grpc/grpc/blob/v1.66.0/examples/cpp/helloworld/greeter_server.cc
        const auto server_address = fmt::format("{}:{}", address, port);
        SimulatorServiceImpl service(job_results_dir, job_queue, logger);

        grpc::EnableDefaultHealthCheckService(true);
        grpc::reflection::InitProtoReflectionServerBuilderPlugin();
        grpc::ServerBuilder builder;
        // Listen on the given address without any authentication mechanism.
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
        // Register "service" as the instance through which we'll communicate with
        // clients. In this case it corresponds to an *synchronous* service.
        builder.RegisterService(&service);
        // Finally assemble the server.
        std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
        LOG_INFO(logger, "Server listening on {}", server_address);

        // Wait for the server to shutdown. Note that some other thread must be
        // responsible for shutting down the server for this call to ever return.
        server->Wait();
    }

    /**
     * @brief Continuously waits for a job to be executable in the job queue and executes the job
     *
     * @param job_results_dir Directory where job results are stored.
     * @param job_queue Job queue to use for managing jobs.
     * @param logger Logger to use for logging messages.
     */

    // TASKS : add comments about worker theread and main thread
    void ExecuteJobs(const std::filesystem::path& job_results_dir, JobQueue& job_queue, quill::Logger* logger)
    {
        LOG_INFO(logger, "Start `ExecuteJobs`");

        while (true)
        {
            JobRequest job_request;
            LOG_INFO(logger, "Waiting for an executable job");
            job_queue.wait_dequeue(job_request);

            LOG_INFO(logger, "Start execution of job {} for user {}", job_request.job_id, job_request.user_id);

            // MYINFO : get GIL
            PyGILState_STATE gstate = PyGILState_Ensure();
            LOG_INFO(logger, "Acquired GIL");

            // MYINFO : import Python module and get function
            PyObject* py_module = PyImport_ImportModule("quantum_simulator");
            if (!py_module)
            {
                PyErr_Print();
                LOG_ERROR(logger, "Failed to import Python module");
                PyGILState_Release(gstate);
                continue;
            }

            LOG_INFO(logger, "First imported Python module");

            PyObject* py_func = PyObject_GetAttrString(py_module, "simulate_quantum_circuit");
            if (!py_func || !PyCallable_Check(py_func))
            {
                PyErr_Print();
                LOG_ERROR(logger, "Failed to get Python function");
                Py_CLEAR(py_module);
                PyGILState_Release(gstate);
                continue;
            }

            LOG_INFO(logger, "Obtained Python function");

            // MYINFO : Prepare arguments for Python function
            const auto json_file_path =
                GetJobFilePath(job_results_dir, job_request.user_id, job_request.job_id, "json");
            constexpr auto TimeoutSeconds = static_cast<std::int32_t>(
                std::chrono::duration_cast<std::chrono::seconds>(MaxJobExecutionTime).count());

            PyObject* py_args = Py_BuildValue(
                "(sssiis)",
                job_request.circuit_language.c_str(),
                job_request.language_version.c_str(),
                job_request.circuit.c_str(),
                job_request.n_shots,
                TimeoutSeconds,
                json_file_path.c_str()
            );

            // MYINFO : Call Python function
            LOG_INFO(logger, "Before PyObject_CallObject");
            PyObject* py_result = PyObject_CallObject(py_func, py_args);
            LOG_INFO(logger, "After PyObject_CallObject");
            Py_CLEAR(py_args);

            if (!py_result)
            {
                PyErr_Print();
                LOG_WARNING(logger, "Simulation failed (exception occurred)");
            }
            else
            {
                PyObject* is_success = PyTuple_GetItem(py_result, 0);
                const char* error_message = PyUnicode_AsUTF8AndSize(PyTuple_GetItem(py_result, 1), nullptr);

                if (is_success == Py_False)
                {
                    LOG_WARNING(logger, "Simulation failed: {}", error_message);
                }
                else
                {
                    LOG_INFO(logger, "Simulation completed successfully");
                }

                // MYINFO : Write error message to error file if simulation failed
                const auto error_file_path =
                    GetJobFilePath(job_results_dir, job_request.user_id, job_request.job_id, "err");
                std::ofstream error_file(error_file_path);
                if (error_file) error_file << error_message;
                Py_CLEAR(py_result);
            }

            Py_CLEAR(py_func);
            Py_CLEAR(py_module);

            LastFinishedJobId = job_request.job_id;

            LOG_INFO(logger, "Completed execution of job {}", job_request.job_id);

            // ===== GIL を解放 =====
            PyGILState_Release(gstate);
        }
    }


    /**
     * @brief Periodically cleans up expired job results.
     *
     * @param job_results_dir Directory where job results are stored.
     * @param logger Logger to use for logging messages.
     */
    void RemoveExpiredResults(const std::filesystem::path& job_results_dir, quill::Logger* logger)
    {
        LOG_INFO(logger, "Start `RemoveExpiredResults`");

        const auto error_file_pattern = std::regex(R"((.*)_(\d+).err)");

        while (true)
        {
            LOG_INFO(logger, "Scanning the result directory: {}", job_results_dir.string());
            for (const auto& error_file : std::filesystem::directory_iterator(job_results_dir))
            {
                const auto error_file_name = error_file.path().filename().string();
                std::match_results<std::string::const_iterator> match_results;
                if (std::regex_match(error_file_name, match_results, error_file_pattern))
                {
                    const auto user_id = match_results[1].str();
                    const auto job_id = static_cast<std::int32_t>(std::stoi(match_results[2].str()));
                    if (ShouldRemoveResult(job_id, error_file.path()))
                    {
                        const auto json_file_path = GetJobFilePath(job_results_dir, user_id, job_id, "json");
                        LOG_NOTICE(logger, "Remove two files, \"{}\" and \"{}\"", json_file_path.string(),
                                   error_file.path().string());
                        std::filesystem::remove(json_file_path);
                        std::filesystem::remove(error_file.path());
                    }
                }
            }

            LOG_INFO(logger, "Waiting for {} seconds",
                     std::chrono::duration_cast<std::chrono::seconds>(ResultsCleanInterval).count());
            std::this_thread::sleep_for(ResultsCleanInterval);
        }
    }
} 

namespace
{
    /**
     * @struct CmdLineOptions
     * @brief Represents command line options.
     */
    struct CmdLineOptions
    {
        /**
         * @brief Server port number to listen for connections.
         */
        std::uint16_t port;

        /**
         * @brief Directory to store job results.
         */
        std::filesystem::path job_results_dir;
    };

    /**
     * @brief Parses command line options.
     *
     * @param argc The number of command line arguments.
     * @param argv Array of command line arguments.
     * @return Parsed command line options.
     */
    CmdLineOptions ParseCmdLineOptions(int argc, const char* argv[])
    {
        CmdLineOptions options;

        namespace bp = boost::program_options;
        auto desc = bp::options_description("Usage");

        desc.add_options()("port,p", bp::value<uint16_t>(&options.port)->required(),
                           "the port number to listen for connections");
        desc.add_options()("results-dir", bp::value<std::filesystem::path>(&options.job_results_dir)->required(),
                           "the directory to store job results");

        try
        {
            bp::variables_map vm;
            bp::store(bp::parse_command_line(argc, argv, desc), vm);
            bp::notify(vm);
        }
        catch (const std::exception& e)
        {
            desc.print(std::cerr);
            std::terminate();
        }

        return options;
    }
}  // namespace

/**
 * @brief Starts listener, worker, and cleaner threads.
 *
 * This function starts three threads:
 * - A listener thread to handle incoming connections.
 * - A worker thread to execute jobs in the job queue.
 * - A cleaner thread to clean up expired job results.
 *
 * @param argc The number of command line arguments.
 * @param argv Array of command line arguments.
 * @return Exit status of the program.
 */
int main(int argc, const char* argv[])
{   
    // Python embedded
    setenv(
    "PYTHONPATH",
    "/work/xg24i001/x10589/Documents_usami/Qiskit/server/src",
    1
    );

    // Python Initialize
    Py_Initialize();

    PyRun_SimpleString("import qiskit");
    PyRun_SimpleString("from qiskit import qasm2, qasm3");
    PyRun_SimpleString("from qiskit_aer import AerSimulator");
    PyRun_SimpleString("qsam2.loads(\"OPENQASM 2; qubit q;\")");
    PyRun_SimpleString("qasm3.loads(\"OPENQASM 3; qubit q;\")");

    // Release the Python GIL
    PyThreadState* mainThreadState = PyEval_SaveThread();

    const auto server_address = std::string("0.0.0.0");

    // parse command line options
    const auto [server_port, job_results_dir] = ParseCmdLineOptions(argc, argv);

    // Create  directories to store job results if they do not exist
    try
    {
        std::filesystem::create_directories(job_results_dir);
    }
    catch (const std::filesystem::filesystem_error& e)
    {
        std::cerr << e.what() << "\n";
        std::terminate();
    }

    // Start logger backend
    quill::Backend::start(quill::BackendOptions{});

    auto console_sink = quill::Frontend::create_or_get_sink<quill::ConsoleSink>("console_sink");

    grpc_qc_simulator::JobQueue job_queue;

    std::thread listener([address = server_address, port = server_port, results_dir = job_results_dir, &job_queue,
                          sink = console_sink]() {
        auto logger = quill::Frontend::create_or_get_logger("listener", sink);
        logger->set_log_level(quill::LogLevel::Info);

        grpc_qc_simulator::RunServer(address, port, results_dir, job_queue, logger);
    });
    std::thread worker([results_dir = job_results_dir, &job_queue, sink = console_sink]() {
        auto logger = quill::Frontend::create_or_get_logger("worker", sink);
        logger->set_log_level(quill::LogLevel::Info);

        grpc_qc_simulator::ExecuteJobs(results_dir, job_queue, logger);
    });
    std::thread cleaner([results_dir = job_results_dir, sink = console_sink]() {
        auto logger = quill::Frontend::create_or_get_logger("cleaner", sink);
        logger->set_log_level(quill::LogLevel::Info);

        grpc_qc_simulator::RemoveExpiredResults(results_dir, logger);
    });

    listener.join();
    worker.join();
    cleaner.join();

    // finalize Python interpreter
    // restore main thread state
    PyEval_RestoreThread(mainThreadState); 

    Py_Finalize();

    return 0;
}
