# クライアントユーザ向けドキュメント

本ドキュメントでは、クライアントコードを作成し実行する手順を説明します。

## Python実行環境の構築

Python仮想環境内で依存パッケージをインストールし、`pb_py`ディレクトリを`PYTHONPATH`に追加します。**本ドキュメントの以降の手順は、全てPython仮想環境内で実行することを前提としています。**

```sh
$ /usr/bin/python3 -m venv .venv
$ . .venv/bin/activate
$ pip install -r examples/requirements.txt
$ export PYTHONPATH="${PWD}/pb_py:${PYTHONPATH}"
```

## [Protocol Buffers定義ファイル](./proto/qc_simulator.proto)のコンパイル

```sh
$ pushd pb_py
$ make
$ popd
```

* 正しく実行されると、`pb_py/`以下に3つのファイル（`qc_simulator_pb2_grpc.py`、`qc_simulator_pb2.py`、`qc_simulator_pb2.pyi`）が生成されます

## サンプルコードの実行

1. Pythonインタプリタを起動する

    ```sh
    $ python
    ```

2. 必要なモジュールをインポートする

    ```py
    from enum import Enum
    import grpc
    import qc_simulator_pb2
    import qc_simulator_pb2_grpc
    ```

3. サーバのアドレスとポート番号、トークンを設定する

    ```py
    SERVER_ADDRESS = "localhost"
    SERVER_PORT = 33351
    TOKEN = "**Paste your token here**"
    ```

4. 実行する量子回路を定義する

    ```py
    circuit_language = "QASM"
    language_version = "3"
    circuit = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[2] qubits;
        bit[2] bits;

        h qubits[0];
        cx qubits[0], qubits[1];
        bits = measure qubits;
    """
    n_shots = 10
    ```

5. サーバにジョブのリクエストを送る

    ```py
    submit_job_request = qc_simulator_pb2.SubmitJobRequest(token=TOKEN, circuit_language=circuit_language, language_version=language_version, circuit=circuit, n_shots=n_shots)
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)
        submit_job_response = stub.SubmitJob(submit_job_request)
    ```

6. ジョブに付与されたIDを表示する

    ```py
    print(f"job_id:{submit_job_response.job_id}")
    ```

7. ジョブの状態および実行結果を問い合わせる

    ```py
    get_result_request = qc_simulator_pb2.GetResultRequest(token=TOKEN, job_id=submit_job_response.job_id)
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)
        get_result_response = stub.GetResult(get_result_request)
    ```

8. サーバからのレスポンスを表示する

    ```py
    class ResponseStatus(Enum):
        UNKNOWN = 0
        QUEUED = 1
        RUNNING = 2
        COMPLETED = 3
        FAILED = 4

    print(f"job_id:{get_result_response.job_id}")
    print(f"status:{ResponseStatus(get_result_response.status).name}")
    print(f"message:{get_result_response.message}")
    print(f"result_json:{get_result_response.result_json}")
    ```

    * `job_id`: ジョブのID
    * `status`：ジョブのステータス
        * `UNKNOWN`：不明
        * `QUEUED`：実行開始前
        * `RUNNING`：実行中
        * `COMPLETED`：実行が正常に終了
        * `FAILED`：実行に失敗して終了
    * `message`：ジョブのステータスに応じたメッセージ
    * `result_json`：シミュレータの実行が終了している場合、シミュレータの実行結果（JSON形式）

## サンプルスクリプトの実行

[サンプルコードの実行](#サンプルコードの実行)に対応するスクリプトは次の2つです。**これらのスクリプトは実行前に編集し、変数`TOKEN`に認証局から発行されたトークンを設定してください。**

* [`submit_job.py`](./examples/submit_job.py): localhostの33351番ポートで接続を待つサーバにジョブのリクエストを送り、ジョブに付与されたIDを出力するPythonスクリプト

    ```sh
    $ python examples/submit_job.py
    ```

* [`get_result.py`](./examples/get_result.py): localhostの33351番ポートで接続を待つサーバにジョブの状態および実行結果を問い合わせ、サーバからのレスポンスを出力するPythonスクリプト

    ```sh
    $ python examples/get_result.py 0 # 0番のジョブの状態を問い合わせる
    ```
