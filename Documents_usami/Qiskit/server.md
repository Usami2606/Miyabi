# サーバ運用者向けドキュメント

本ドキュメントでは、Dockerを用いてサーバを実行する手順を説明します。

## Dockerコンテナでサーバを起動する方法　

1. Dockerイメージ`sim_server`を作成する

    ```sh
    $ docker build -t sim_server .
    ```

2. Dockerイメージ`sim_server`からコンテナ`sim_server_container`を作成し、サーバを起動する

    ```sh
    $ docker run --detach --name sim_server_container -p 33351:33351 sim_server
    ```

    * `-p <host port>:<container port>`：ホストマシンのポート`<host port>`番とコンテナのポート`<container port>`番をバインドする
        * `-p 33351:33351`の指定により、ホストマシンの33351番ポートへアクセスすると、コンテナの33351番ポートへアクセスすることになる

## サーバのログを確認する方法

```sh
$ docker logs sim_server_container
```

## サーバを停止する方法

1. コンテナ`sim_server_container`のステータスが`Up`であることを確認する

    ```sh
    $ docker ps
    ```

2. `sim_server_container`を停止する

    ```sh
    $ docker stop sim_server_container
    ```

3. `sim_server_container`がコンテナ一覧から無くなったことを確認する

    ```sh
    $ docker ps
    ```
