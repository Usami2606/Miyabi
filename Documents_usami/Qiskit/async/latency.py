import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from submit_job import submit_job
from get_result import get_result
from enum import Enum
from get_result import ResponseStatus

circuit = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
bit[2] b;

h q[0];
cx q[0], q[1];
measure q[0] -> b[0];
measure q[1] -> b[1];
"""

n_shots_list = [10, 100, 500, 1000]

def run_job(n_shots):
    future = submit_job("QASM", "3", circuit, n_shots)
    job_response = future.result()  # ジョブIDを取得
    job_id = job_response.job_id
    print(f"[Submit] n_shots={n_shots}, job_id={job_id}")

    while True:
        status, _ = get_result(job_id)
        if status == ResponseStatus.COMPLETED:
            break
        elif status == ResponseStatus.FAILED:
            raise RuntimeError(f"Job {job_id} failed")
        time.sleep(0.01)
    return job_id

def main():
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_job, n) for n in n_shots_list]

        for future in as_completed(futures):
            job_id = future.result()
            print(f"Job {job_id} finished")

    elapsed = time.time() - start_time
    print(f"All jobs completed in {elapsed:.3f} s")

if __name__ == "__main__":
    main()
