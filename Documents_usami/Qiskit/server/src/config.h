#ifndef _CONFIG_H_
#define _CONFIG_H_

#include <chrono>

namespace grpc_qc_simulator
{
    /**
     * @brief Time after a job is finished until the job result is expired.
     */
    constexpr auto JobResultExpirationTime = std::chrono::minutes{60};

    /**
     * @brief Time after a job is finished until the job result can be deleted.
     */
    constexpr auto JobResultDeletionTime = JobResultExpirationTime + std::chrono::minutes{5};

    // Job results should be deleted after they are expired.
    static_assert(JobResultDeletionTime > JobResultExpirationTime);

    /**
     * @brief Interval at which the server cleans up deletable job results.
     */
    constexpr auto ResultsCleanInterval = std::chrono::minutes{60};

    /**
     * @brief The maximum execution time of a job.
     */
    constexpr auto MaxJobExecutionTime = std::chrono::minutes{30};

    /**
     * @brief Valid issuer of the JWT.
     */
    constexpr auto JWTIssuer = "https://idp.qc.r-ccs.riken.jp/realms/jhpc-quantum";

    /**
     * @brief Public key of the JWT verification.
     */
    constexpr auto JWTPublicKey = R"(
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE6rJrTxR4cWehE5TLPJAjB6zXM20qDt6q2BmSucxZ3XKI9cxhkbPhj1WykrABoBJO/nSRxNlcx3CTw+IKLCx3rw==
-----END PUBLIC KEY-----
)";

    /**
     * @brief Tolerance for JWT expiration time.
     *
     * @note Temporarily set to a large value to bypass expiration checks; should be adjusted to a reasonable value.
     */
    constexpr auto JWTExpirationTimeTolerance = std::chrono::seconds{1000000000};

}  // namespace grpc_qc_simulator

#endif  // _CONFIG_H_
