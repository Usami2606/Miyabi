#ifndef _JWT_H_
#define _JWT_H_

#include <jwt-cpp/jwt.h>
#include <chrono>
#include "config.h"

namespace grpc_qc_simulator
{
    /**
     * @brief Decodes a JSON Web Token (JWT) and verifies it.
     *
     * @param str_token The JSON Web Token to be decoded and verified.
     * @return Decoded JSON Web Token on success.
     * @throws std::invalid_argument if the token is not in correct format.
     * @throws std::runtime_error if decoding fails.
     * @throws std::system_error if verification fails.
     */
    inline auto DecodeToken(const std::string& str_token)
    {
        static const auto Verifier =
            jwt::verify()
                .with_issuer(JWTIssuer)
                .expires_at_leeway(std::chrono::duration_cast<std::chrono::seconds>(JWTExpirationTimeTolerance).count())
                .allow_algorithm(jwt::algorithm::es256{JWTPublicKey});
        try
        {
            const auto decoded_token = jwt::decode(str_token);
            Verifier.verify(decoded_token);
            return decoded_token;
        }
        catch (...)
        {
            throw;
        }
    }
}  // namespace grpc_qc_simulator

#endif  // _JWT_H_
