import pytest
import grpc
import qc_simulator_pb2
import qc_simulator_pb2_grpc

SERVER_ADDRESS = "localhost"
SERVER_PORT = 33351

VALID_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"

# Delete the first . in the string
INVALID_FORMAT_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"

# Capitalize the signiture
INVALID_SIGNITURE_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.EZDJI9V2W8TRNXTR7AALA9VNBUR98KN49TIJ88KABTZI2LCE9I9ZJKNXLN07Q0SESP-8ZILKILFPBAVCDC0B8Q"


@pytest.mark.parametrize(
    ("token", "error_code", "error_message"),
    [
        (
            INVALID_FORMAT_TOKEN,
            grpc.StatusCode.INVALID_ARGUMENT,
            "invalid token supplied",
        ),
        (INVALID_SIGNITURE_TOKEN, grpc.StatusCode.UNAUTHENTICATED, "invalid signature"),
    ],
)
def test_invalid_token(token: str, error_code: grpc.StatusCode, error_message: str):
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)

        with pytest.raises(grpc.RpcError) as e:
            stub.SubmitJob(
                qc_simulator_pb2.SubmitJobRequest(
                    token=token,
                    circuit_language="QASM",
                    language_version="3",
                    circuit="""
                OPENQASM 3.0;
                include "stdgates.inc";

                qubit[2] qubits;
                bit[2] bits;

                h qubits[0];
                cx qubits[0], qubits[1];
                bits = measure qubits;
                    """,
                    n_shots=10,
                )
            )
        assert e.value.code() == error_code
        assert e.value.details() == error_message


def test_valid_token():
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)

        response = stub.SubmitJob(
            qc_simulator_pb2.SubmitJobRequest(
                token=VALID_TOKEN,
                circuit_language="QASM",
                language_version="3",
                circuit="""
            OPENQASM 3.0;
            include "stdgates.inc";

            qubit[2] qubits;
            bit[2] bits;

            h qubits[0];
            cx qubits[0], qubits[1];
            bits = measure qubits;
                """,
                n_shots=10,
            )
        )
        assert response.job_id >= 0
