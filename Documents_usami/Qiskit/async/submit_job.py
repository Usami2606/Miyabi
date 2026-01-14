import grpc
import qc_simulator_pb2
import qc_simulator_pb2_grpc
from concurrent.futures import Future

SERVER_ADDRESS = "172.16.1.2"
#SERVER_ADDRESS = "localhost"
SERVER_PORT = 33351
TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"


def submit_job(
    circuit_language: str, language_version: str, circuit: str, n_shots: int
):
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)

        future = stub.SubmitJob.future(
            qc_simulator_pb2.SubmitJobRequest(
                token=TOKEN,
                circuit_language=circuit_language,
                language_version=language_version,
                circuit=circuit,
                n_shots=n_shots,
            )
        )
        return(future)
    


if __name__ == "__main__":
    circuit_language = "QASM"
    language_version = "3"
    circuit = """
        OPENQASM 3.0;
    include "stdgates.inc";

    qubit[8] q;
    bit[8] b;

    // 重ね合わせ
    h q[0]; h q[1]; h q[2]; h q[3];
    h q[4]; h q[5]; h q[6]; h q[7];

    // 多層エンタングルメント
    cx q[0], q[1];
    cx q[1], q[2];
    cx q[2], q[3];
    cx q[3], q[4];
    cx q[4], q[5];
    cx q[5], q[6];
    cx q[6], q[7];
    cx q[7], q[0];

    // 測定
    measure q[0] -> b[0];
    measure q[1] -> b[1];
    measure q[2] -> b[2];
    measure q[3] -> b[3];
    measure q[4] -> b[4];
    measure q[5] -> b[5];
    measure q[6] -> b[6];
    measure q[7] -> b[7];
    """
    n_shots = 10

    submit_job(circuit_language, language_version, circuit, n_shots)
