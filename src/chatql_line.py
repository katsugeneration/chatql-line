# coding=utf-8
#
# Licensed under the MIT License
"""Line Webhook Server."""
import os
import logging
from flask import Flask, request, abort

import chatql
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
app.logger.setLevel(logging.INFO)

client = chatql.mongodb_client.MongoClient(
            **{"db": os.environ.get('MONGO_DB', 'chatql'),
               "host": os.environ.get('MONGO_HOST', '127.0.0.1'),
               "port": int(os.environ.get('MONGO_PORT', '27017')),
               "username": os.environ.get('MONGO_USER'),
               "password": os.environ.get('MONGO_PASSWORD')})
engine = chatql.engine.DialogEngine(client)
client.import_scenario("scenario.json")

chatql_query = '''
    query getResponse($request: String!) {
        response(request: $request) {
            id
            text
        }
    }
'''


@app.route("/callback", methods=['POST'])
def callback():
    """Line Webhook interface."""
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Text Message Handler."""
    if event.reply_token == '00000000000000000000000000000000':
        return

    text = event.message.text
    result = chatql.schema.execute(
                chatql_query,
                context={'engine': engine},
                variables={'request': text})

    if result.errors is not None:
        print(result.errors)
        abort(500)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result.data['response']['text']))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
