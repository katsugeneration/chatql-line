# chatql-line
ChatQL LINE Webhook Interface


## 使い方
下記のコマンドでサーバーが起動します。
`poetry run python src/chatql_line.py`

また、以下の値をあらかじめ環境変数に設定しておく必要があります。
- `LINE_CHANNEL_SECRET`: LINE Messaging APIのChannel Secret
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Messaging APIのアクセストークン
- `MONGO_HOST`: mongodbのホスト名
- `MONGO_PORT`: mongodbのポート番号
- `MONGO_DB`: mongodbのデータベース名
- `MONGO_USER`: mongodbのユーザー名
- `MONGO_PASSWORD`: mongodbのパスワード
- `SCENARIO_DOWNLOAD_COMMAND`: シナリオのダウンロードコマンド。 `scenario.json` としてダウンロードする必要があります