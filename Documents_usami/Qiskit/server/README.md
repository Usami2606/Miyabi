# サーバ設計書

本ドキュメントは、サーバの設計についてその詳細を述べたものです。

## 設計の概要

* サーバプログラムはC++で記述されています。
* ジョブのリクエストを受け取る`SubmitJob`およびジョブの実行結果を返す`GetResult`の2種類のgRPCサービスを提供します。
* 量子回路シミュレータとして[Qiskit Aer](https://qiskit.github.io/qiskit-aer/)を使用します。
* 量子回路の記述言語として[OpenQASM](https://openqasm.com/)のバージョン2および3に対応しています。

## gRPCサービス

以下の2つのgRPCサービスを提供します。

* `SubmitJob`: クライアントから送られたジョブの実行リクエストをキューに入れ、レスポンスとしてジョブのIDを返す。
    * リクエスト
        * `token`: 認証局から発行されたトークン（JSON Web Token）。トークンが不正な場合、gRPCエラーを返す。
        * `circuit_language`および `language_version`: `circuit`を記述する言語とバージョン。現在サポートしている`circuit_language`は`"QASM"`、`language_version`は`"2"`または`"3"`。サポートしていない言語またはバージョンが指定された場合、**gRPCエラーは返さず**、シミュレータの実行が失敗する。
        * `circuit`: シミュレータで実行する量子回路。
        * `n_shots`: ショット数。
    * 成功時のレスポンス
        * `job_id`: サーバが起動してからジョブが投入された順に、0,1,2,...というように順番に割り当てられるジョブのID。
    * 失敗時のレスポンス
        * gRPCエラー: 失敗理由に応じて以下のいずれかの[ステータスコード](https://grpc.io/docs/guides/status-codes/#the-full-list-of-status-codes)を持つ
            * `INVALID_ARGUMENT`: トークンのフォーマットが不正な場合
            * `UNAUTHENTICATED`: トークンの認証に失敗した場合
            * `INTERNAL`: サーバ内部でエラーが発生した場合
            * `UNKNOWN`: 失敗の理由が不明な場合
* `GetResult`: クライアントから要求されたジョブの状態と実行結果を返す。
    * リクエスト
        * `token`: 認証局から発行されたトークン（JSON Web Token）。トークンが不正な場合、gRPCエラーを返す。
        * `job_id`: 結果を問い合わせるジョブのID。指定されたIDが不正な場合、gRPCエラーを返す。
    * 成功時のレスポンス
        * `job_id`: ジョブのID。
        * `status`：ジョブの現在の状態に応じて、以下のいずれかになる。
            * `UNKNOWN`：不明
            * `QUEUED`：実行開始前
            * `RUNNING`：実行中
            * `COMPLETED`：実行が正常に終了
            * `FAILED`：実行に失敗して終了
        * `message`：ジョブのステータスに応じたメッセージ。`status`が`FAILED`の場合、エラーメッセージが入る。
        * `result_json`：シミュレータの実行が終了している場合、JSON形式のシミュレータの実行結果が入る。終了していない場合は、空文字列となる。
    * 失敗時のレスポンス
        * gRPCエラー: 失敗理由に応じて以下のいずれかの[ステータスコード](https://grpc.io/docs/guides/status-codes/#the-full-list-of-status-codes)を持つ
            * `INVALID_ARGUMENT`: トークンのフォーマットが不正な場合、ジョブIDが無効な値である場合、ジョブの投入ユーザと問い合わせをおこなったユーザが異なる場合
            * `UNAUTHENTICATED`: トークンの認証に失敗した場合
            * `INTERNAL`: サーバ内部でエラーが発生した場合
            * `UNKNOWN`: 失敗の理由が不明な場合

[Protocol Buffersの定義ファイル](../proto/qc_simulator.proto)

## API Reference

各関数やクラスのドキュメントを参照するには、[こちらのHTMLファイル](../docs/html/index.html)をブラウザで開いてください。

API referenceを生成し直す場合、[Doxygen](https://github.com/doxygen/doxygen/releases/tag/Release_1_10_0)をインストールした後、**プロジェクトのルートディレクトリで**次のコマンドを実行してください。

```sh
$ doxygen
```

## ファイル構成

```
server/
├── README.md
└── src/
    ├── config.h
    ├── job_utils.h
    ├── jwt.h
    ├── main.cpp
    ├── quantum_simulator.py
    └── server.h
```

* `README.md`: 本ドキュメント
* `src/config.h`: サーバの動作に関するパラメータを設定するファイル
* `src/job_utils.h`: ジョブに関するユーティリティ関数を定義するファイル
* `src/jwt.h`: JSON Web Token (JWT) 関連の関数を定義するファイル
* `src/main.cpp`: サーバのメインプログラム
* `src/quantum_simulator.py`: 量子回路シミュレータ[Qiskit Aer](https://qiskit.github.io/qiskit-aer/)を使用するPythonコード
* `src/server.h`: gRPCサーバの実装ファイル
