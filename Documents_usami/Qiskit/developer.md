# サーバ開発者向けドキュメント

本ドキュメントは、サーバ開発者向けのドキュメントです。

* [ローカル環境でサーバを実行する手順](#ローカル環境でサーバを実行する手順)
* [サーバのテスト方法](#サーバのテスト方法)
* [ディレクトリ構成](#ディレクトリ構成)

## ローカル環境でサーバを実行する手順

1. `externals/`以下に[vcpkg](https://vcpkg.io/en/)をダウンロードする

    * Gitリポジトリの場合

        ```sh
        $ git submodule update --init
        ```

    * Gitリポジトリでない場合

        ```sh
        $ git clone https://github.com/microsoft/vcpkg.git externals/vcpkg
        ```

2. Pythonの仮想環境を作成し、ビルドに必要なパッケージをインストールする

    ```sh
    $ /usr/bin/python3 -m venv .venv
    $ . .venv/bin/activate
    $ pip install -r requirements.txt
    ```

3. サーバプログラムをビルドする

    ```sh
    $ rm -rf build
    $ cmake -DCMAKE_TOOLCHAIN_FILE=externals/vcpkg/scripts/buildsystems/vcpkg.cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=TRUE -DCMAKE_BUILD_TYPE=Release -S . -B build
    $ cmake --build build --clean-first
    ```

    * ビルド時に[protoファイル](./proto/qc_simulator.proto)がコンパイルされ、`pb_cpp/`以下に4つのファイル（`qc_simulator.grpc.pb.cc`、`qc_simulator.grpc.pb.h`、`qc_simulator.pb.cc`、`qc_simulator.pb.h`）が生成される

4. サーバを起動する

    ```sh
    $ export PYTHONPATH="${PWD}/server/src:${PYTHONPATH}"
    $ ./build/Release/bin/server --port 33351 --results-dir <path/to/job_results_dir>
    ```

    * `<path/to/job_results_dir>`：ジョブの実行結果を保存するディレクトリ
    * 33351番ポートでクライアントからの接続を待つ

## サーバのテスト方法

[Python実行環境の構築](client.md#python実行環境の構築)に従って環境を構築した後、仮想環境内で次のコマンドを実行してください。

```sh
$ pytest test
```

## ディレクトリ構成

```
.
├── cmake/
├── docs/
├── examples/
├── externals/
├── pb_cpp/
├── pb_py/
├── proto/
├── server/src/
└── test/
```

* `cmake`: CMakeの設定ファイルを置くディレクトリ
* `docs`: ドキュメントファイルの生成先ディレクトリ
* `examples`: クライアントコードのサンプルを置くディレクトリ
* `externals`: 外部モジュールを置くディレクトリ
* `pb_cpp`: Protocol Buffersの定義ファイルのコンパイル結果のC++コードが生成されるディレクトリ
* `pb_py`: Protocol Buffersの定義ファイルのコンパイル結果のPythonコードが生成されるディレクトリ
* `server/src`: サーバプログラムのソースファイルを置くディレクトリ
* `test`: サーバのテストコードを置くディレクトリ
