import time
from submit_job import submit_job
from get_result import get_result
from enum import Enum
from get_result import ResponseStatus

# テスト用の簡易量子回路（2 qubit, 2 gate）
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
""".strip()

# circuit = """
# OPENQASM 3.0;
# include "stdgates.inc";
# qubit[1] q;
# bit[1] b;
# h q[0];
# measure q[0] -> b[0];
# """.strip()

# n_shots を変えて計測
# for n_shots in [1, 100, 1000, 10000]:
#     print(f"\n=== Testing n_shots = {n_shots} ===")
#     start_time = time.time()

#     # 1. ジョブ送信
#     job_id = submit_job("QASM", "3", circuit, n_shots)
#     print("JobID:", job_id)
#     while True:
#         status, result = get_result(job_id)
#         if status == ResponseStatus.COMPLETED:
#             break
#         elif status == ResponseStatus.FAILED:
#             raise RuntimeError(f"Job {job_id} failed")
#         else:
#             continue
#             #print(f"Job {job_id} is {status.name}, waiting...")
#         time.sleep(0.05)

#     end_time = time.time()
#     elapsed = end_time - start_time

#     # 3. 結果表示
#     print(f"Elapsed time for n_shots={n_shots}: {elapsed:.3f} s")


n_calls_list = [1, 10, 50, 100]

for n_calls in n_calls_list:
    print(f"\n=== Testing {n_calls} calls ===")
    start_time = time.time()

    for _ in range(n_calls):
        job_id = submit_job("QASM", "3", circuit, 1)  
        while True:
            status, _ = get_result(job_id)
            if status == ResponseStatus.COMPLETED:
                break
            elif status == ResponseStatus.FAILED:
                raise RuntimeError(f"Job {job_id} failed")
            time.sleep(1)

    end_time = time.time()
    print(f"Elapsed time for {n_calls} calls: {end_time - start_time:.3f} s")

    avg_time = (end_time - start_time) / n_calls
    print(f"Average time per RPC: {avg_time:.4f} s")