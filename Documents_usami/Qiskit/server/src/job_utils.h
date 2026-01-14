#ifndef _JOB_UTILS_H_
#define _JOB_UTILS_H_

#include <fmt/format.h>
#include <readerwriterqueue.h>
#include <atomic>
#include <filesystem>
#include "config.h"

namespace grpc_qc_simulator
{
    /**
     * @brief Global variable to keep track of the last finished job ID.
     */
    extern std::atomic_int32_t LastFinishedJobId;

    /**
     * @struct JobRequest
     * @brief Represents a job request submitted by a user.
     */
    struct JobRequest
    {
        /**
         * @brief User ID of the submitting user.
         */
        std::string user_id;

        /**
         * @brief Job ID of the submitted job.
         */
        std::int32_t job_id;

        /**
         * @brief Programming language used to describe a quantum circuit.
         */
        std::string circuit_language;

        /**
         * @brief Version of the programming language.
         */
        std::string language_version;

        /**
         * @brief Quantum circuit written in the specified language.
         */
        std::string circuit;

        /**
         * @brief Number of shots to run the quantum circuit.
         */
        std::int32_t n_shots;
    };

    /**
     * @brief Thread-safe queue for job requests.
     *
     * @note It only supports a two-thread use case with one thread for enqueueing and one thread for dequeueing.
     */
    using JobQueue = moodycamel::BlockingReaderWriterQueue<JobRequest>;

    /**
     * @brief Returns the file path for a job file.
     *
     * @param job_results_dir Directory where job results are stored.
     * @param user_id User ID of the user who submitted the job.
     * @param job_id Job ID of the job.
     * @param ext File extension (e.g., "json", "txt", etc.).
     * @return File path for the job file.
     */
    [[nodiscard]] inline std::filesystem::path GetJobFilePath(const std::filesystem::path& job_results_dir,
                                                              std::string_view user_id, const std::int32_t job_id,
                                                              std::string_view ext)
    {
        const auto job_file_name = fmt::format("{}_{}.{}", user_id, job_id, ext);
        return job_results_dir / job_file_name;
    }

    /**
     * @brief Checks if a job is queued (i.e., waiting to be executed).
     *
     * @param job_id Job ID.
     * @return True if the job is queued, false otherwise.
     */
    [[nodiscard]] inline bool IsQueued(const std::int32_t job_id) { return job_id > LastFinishedJobId + 1; }

    /**
     * @brief Checks if a job is currently running.
     *
     * @param job_id Job ID.
     * @return True if the job is running, false otherwise.
     */
    [[nodiscard]] inline bool IsRunning(const std::int32_t job_id) { return job_id == LastFinishedJobId + 1; }

    /**
     * @brief Checks if a job has finished.
     *
     * @param job_id Job ID.
     * @return True if the job has finished, false otherwise.
     */
    [[nodiscard]] inline bool IsFinished(const std::int32_t job_id) { return job_id <= LastFinishedJobId; }

    namespace detail
    {
        /**
         * @brief Returns the elapsed time since a job finished execution.
         *
         * @param error_file_path File path to the job's error file.
         * @return Elapsed time since the job finished execution.
         */
        inline auto GetElapsedTimeSinceJobFinished(const std::filesystem::path& error_file_path)
        {
            const auto current_time = std::filesystem::file_time_type::clock::now();
            return current_time - std::filesystem::last_write_time(error_file_path);
        }

        /**
         * @brief Checks if a job result has expired.
         *
         * @param job_id Job ID.
         * @param error_file_path File path to the job's error file.
         * @return True if the job result has expired, false otherwise.
         */
        inline bool IsResultExpired(const std::int32_t job_id, const std::filesystem::path& error_file_path)
        {
            return IsFinished(job_id) && GetElapsedTimeSinceJobFinished(error_file_path) > JobResultExpirationTime;
        }

    }  // namespace detail

    /**
     * @brief Checks if a job result should be deleted.
     *
     * @param job_id Job ID.
     * @param error_file_path File path to the job's error file.
     * @return True if the job result can be deleted, false otherwise.
     */
    inline bool ShouldRemoveResult(const std::int32_t job_id, const std::filesystem::path& error_file_path)
    {
        return IsFinished(job_id) && detail::GetElapsedTimeSinceJobFinished(error_file_path) > JobResultDeletionTime;
    }

    /**
     * @brief Validates a job result request.
     *
     * @param user_id User ID of the requesting user.
     * @param job_id Job ID of the requested job.
     * @param min_valid_job_id Minimum valid job ID.
     * @param max_valid_job_id Maximum valid job ID.
     * @param job_results_dir Directory where job results are stored.
     * @throws std::invalid_argument if the job result request is invalid.
     */
    inline void ValidateJobResultRequest(std::string_view user_id, const std::int32_t job_id,
                                         const std::int32_t min_valid_job_id, const std::int32_t max_valid_job_id,
                                         const std::filesystem::path& job_results_dir)
    {
        const auto error_file_path = GetJobFilePath(job_results_dir, user_id, job_id, "err");
        if (job_id < min_valid_job_id || max_valid_job_id < job_id || !std::filesystem::exists(error_file_path) ||
            detail::IsResultExpired(job_id, error_file_path))
        {
            throw std::invalid_argument(
                fmt::format("invalid UserID and JobID combination: UserID = {}, JobID = {}", user_id, job_id));
        }
    }

}  // namespace grpc_qc_simulator

#endif  // _JOB_UTILS_H_
