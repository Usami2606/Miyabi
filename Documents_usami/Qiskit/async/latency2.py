import grpc
import qc_simulator_pb2
import qc_simulator_pb2_grpc
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

SERVER_ADDRESS = "172.16.1.2"
SERVER_PORT = 33351
TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"

# --- 回路例 ---
CIRCUIT = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[4] q;
bit[4] b;

h q[0]; h q[1]; h q[2]; h q[3];
cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];

measure q[0] -> b[0];
measure q[1] -> b[1];
measure q[2] -> b[2];
measure q[3] -> b[3];
"""
n_shots_list = [1, 100, 1000, 10000]
def wait_for_result(job_id):
    """非同期で結果が返ってくるまで待機"""
    start_poll = time.time()
    while True:
        status, result = get_result(job_id)  # get_result が (status, result) を返すように変更
        if status == ResponseStatus.COMPLETED.name:
            break
        elif status == ResponseStatus.FAILED.name:
            raise RuntimeError(f"Job {job_id} failed")
        time.sleep(0.05)
    end_poll = time.time()
    return job_id, end_poll - start_poll

def main():
    for n_shots in n_shots_list:
        print(f"\n=== Testing n_shots = {n_shots} ===")
        start_total = time.time()

        # submit は直列化
        job_id = submit_job("QASM", "3", circuit, n_shots)
        print("JobID:", job_id)

        # get_result を非同期で待つ
        with ThreadPoolExecutor() as executor:
            future = executor.submit(wait_for_result, job_id)
            job_id, poll_time = future.result()

        end_total = time.time()
        elapsed = end_total - start_total

        print(f"Elapsed total time for n_shots={n_shots}: {elapsed:.3f} s")
        print(f"Polling time for n_shots={n_shots}: {poll_time:.3f} s")

if __name__ == "__main__":
    main()