#ifndef _SERVER_H_
#define _SERVER_H_

#include <fmt/format.h>
#include <quill/LogMacros.h>
#include <quill/Logger.h>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include "job_utils.h"
#include "jwt.h"
#include "qc_simulator.grpc.pb.h"

namespace grpc_qc_simulator
{
    /**
     * @brief Creates a new file.
     *
     * @param file_path Path of the file to be created.
     * @throws std::runtime_error if the file cannot be created.
     */
    inline void CreateFile(const std::filesystem::path& file_path)
    {
        auto file = std::ofstream(file_path);
        if (!file)
        {
            throw std::runtime_error(fmt::format("Failed to create a file:{}", file_path.string()));
        }
        file.close();
    }

    /**
     * @brief Reads the contents of a file into a string.
     *
     * @param file_path Path of the file to be read.
     * @return Contents of the file.
     * @throws std::runtime_error if the file cannot be opened.
     */
    inline std::string ReadFileIntoString(const std::filesystem::path& file_path)
    {
        auto file = std::ifstream(file_path);
        if (!file)
        {
            throw std::runtime_error(fmt::format("Failed to open a file: {}", file_path.string()));
        }
        std::stringstream buffer;
        buffer << file.rdbuf();
        file.close();
        return buffer.str();
    }

    /**
     * @class SimulatorServiceImpl
     * @brief Implementation of SimulatorService.
     */
    class SimulatorServiceImpl : public qc_simulator::SimulatorService::Service
    {
    public:
        /**
         * @brief Constructs a new SimulatorServiceImpl object.
         *
         * @param job_results_dir Directory where job results are stored.
         * @param job_queue Job queue to use for managing jobs.
         * @param logger Logger to use for logging messages.
         */
        explicit SimulatorServiceImpl(const std::filesystem::path& job_results_dir, JobQueue& job_queue,
                                      quill::Logger* logger)
            : job_results_dir(job_results_dir), job_queue_(job_queue), logger(logger) {};

    private:
        /**
         * @brief Directory where job results are stored.
         */
        const std::filesystem::path job_results_dir;

        /**
         * @brief Job queue to use for managing jobs.
         */
        JobQueue& job_queue_;

        /**
         * @brief Job ID to be assigned to the next submitted job.
         */
        std::int32_t next_job_id_ = 0;

        /**
         * @brief Logger to use for logging messages.
         */
        quill::Logger* const logger;

        /**
         * @brief Catches an exception and converts it to a gRPC status.
         *
         * @return grpc::Status object.
         */
        grpc::Status HandleException() noexcept
        {
            try
            {
                throw;
            }
            catch (const std::invalid_argument& e)
            {
                LOG_WARNING(logger, "Error: {}", e.what());
                return {grpc::StatusCode::INVALID_ARGUMENT, e.what()};
            }
            catch (const std::system_error& e)
            {
                LOG_WARNING(logger, "Error: {}", e.what());
                return {grpc::StatusCode::UNAUTHENTICATED, e.what()};
            }
            catch (const std::exception& e)
            {
                LOG_CRITICAL(logger, "Error: {}", e.what());
                return {grpc::StatusCode::INTERNAL, "internal error occurred"};
            }
            catch (...)
            {
                const auto error_message = "unknown error occurred";
                LOG_CRITICAL(logger, "Error: {}", error_message);
                return {grpc::StatusCode::UNKNOWN, error_message};
            }
        }

        /**
         * @brief Submits a job to the server.
         *
         * This function authenticates the request token, adds the job to the job queue, and returns the job ID.
         *
         * @param context gRPC server context.
         * @param request Request for SubmitJob.
         * @param response Response for SubmitJob.
         * @return grpc::Status object.
         */
        grpc::Status SubmitJob(grpc::ServerContext* context, const qc_simulator::SubmitJobRequest* request,
                               qc_simulator::SubmitJobResponse* response) override
        {
            LOG_INFO(logger, "Received `SubmitJob` request from {}", context->peer());

            try
            {
                LOG_INFO(logger, "Authenticate a given token");
                const auto decoded_token = DecodeToken(request->token());
                const auto user_id = decoded_token.get_payload_claim("sub").as_string();

                const auto json_file_path = GetJobFilePath(job_results_dir, user_id, next_job_id_, "json");
                const auto error_file_path = GetJobFilePath(job_results_dir, user_id, next_job_id_, "err");

                LOG_NOTICE(logger, "Create two files, \"{}\" and \"{}\"", json_file_path.string(),
                           error_file_path.string());
                CreateFile(json_file_path);
                CreateFile(error_file_path);

                LOG_INFO(logger,
                         "Add job {} to the queue (circuit_language: {}, language_version: {}, circuit: {} bytes, "
                         "n_shots: {})",
                         next_job_id_, request->circuit_language(), request->language_version(),
                         request->circuit().size(), request->n_shots());
                job_queue_.enqueue(JobRequest{
                    .user_id = user_id,
                    .job_id = next_job_id_,
                    .circuit_language = request->circuit_language(),
                    .language_version = request->language_version(),
                    .circuit = request->circuit(),
                    .n_shots = request->n_shots(),
                });

                response->set_job_id(next_job_id_);
                ++next_job_id_;
                LOG_INFO(logger, "Return a response for `SubmitJob` to {}", context->peer());
                return grpc::Status::OK;
            }
            catch (...)
            {
                return HandleException();
            }
        }

        /**
         * @brief Queries the status and result of a job.
         *
         * This function validates the request, checks the job status, and returns the job result if available.
         *
         * @param context gRPC server context.
         * @param request Request for GetResult.
         * @param response Response for GetResult.
         * @return grpc::Status object.
         */
        grpc::Status GetResult(grpc::ServerContext* context, const qc_simulator::GetResultRequest* request,
                               qc_simulator::GetResultResponse* response) override
        {
            LOG_INFO(logger, "Received `GetResult` request from {}", context->peer());

            try
            {
                LOG_INFO(logger, "Authenticate a given token");
                const auto decoded_token = DecodeToken(request->token());
                const auto user_id = decoded_token.get_payload_claim("sub").as_string();

                LOG_INFO(logger, "Validate UserID: {} and JobID: {}", user_id, request->job_id());
                ValidateJobResultRequest(user_id, request->job_id(), 0, next_job_id_ - 1, job_results_dir);

                LOG_INFO(logger, "Get the current status of job {}", request->job_id());
                response->set_job_id(request->job_id());
                if (IsQueued(request->job_id()))
                {
                    response->set_status(qc_simulator::GetResultResponse::Status::GetResultResponse_Status_QUEUED);
                    response->set_message("Not started");
                }
                else if (IsRunning(request->job_id()))
                {
                    response->set_status(qc_simulator::GetResultResponse::Status::GetResultResponse_Status_RUNNING);
                    response->set_message("In progress");
                }
                else
                {
                    const auto error_file_path = GetJobFilePath(job_results_dir, user_id, request->job_id(), "err");
                    const auto error_string = ReadFileIntoString(error_file_path);
                    if (error_string.empty())
                    {
                        response->set_status(
                            qc_simulator::GetResultResponse::Status::GetResultResponse_Status_COMPLETED);
                        response->set_message("Completed successfully");
                    }
                    else
                    {
                        response->set_status(qc_simulator::GetResultResponse::Status::GetResultResponse_Status_FAILED);
                        response->set_message(error_string);
                    }
                    const auto json_file_path = GetJobFilePath(job_results_dir, user_id, request->job_id(), "json");
                    response->set_result_json(ReadFileIntoString(json_file_path));

                    LOG_NOTICE(logger, "Remove two files, \"{}\" and \"{}\"", json_file_path.string(),
                               error_file_path.string());
                    std::filesystem::remove(json_file_path);
                    std::filesystem::remove(error_file_path);
                }

                LOG_INFO(logger, "Return a response for `GetResult` to {}", context->peer());
                return grpc::Status::OK;
            }
            catch (...)
            {
                return HandleException();
            }
        }
    };
}  // namespace grpc_qc_simulator

#endif  // _SERVER_H_
