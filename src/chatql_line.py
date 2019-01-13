# coding=utf-8
#
# Licensed under the MIT License
"""Line Webhook Server."""
import os
import json
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


def _create_user(**attributes):
    """Create chatql managed user.

    Args:
        attributes (dict): (Optional) user attributes dictionary
    Return:
        ID (str): User ID string managed chatql
    """
    query = '''
        mutation createUser($optionalArgs: String) {
            createUser(optionalArgs: $optionalArgs) {
                user {
                    id
                }
            }
        }
    '''
    result = chatql.schema.execute(
                query,
                context={'engine': engine},
                variables={"optionalArgs": json.dumps(attributes)})

    if result.errors is not None:
        app.logger.error(result.errors)
        abort(500)
    return result.data['createUser']['user']['id']


def _get_user(**attributes):
    """Get chatql managed user.

    Args:
        attributes (dict): (Optional) user attributes dictionary
    Return:
        ID (str): User ID string managed chatql. return None, case user does not exist.
    """
    query = '''
        query getUser($optionalArgs: String) {
            user(optionalArgs: $optionalArgs) {
                id
            }
        }
    '''
    result = chatql.schema.execute(
                query,
                context={'engine': engine},
                variables={"optionalArgs": json.dumps(attributes)})

    if result.errors is not None:
        app.logger.error(result.errors)
        abort(500)

    if result.data['createUser']['user']['id'] is None:
        return _create_user(**attributes)
    return result.data['createUser']['user']['id']


def _generate_response(request, user_id):
    """Generate response with chatql.

    Args:
        request (str): User input text
        user_id (str): User ID string managed chatql
    Return:
        response (str): Response string
    """
    query = '''
        query getResponse($request: String!, $user: ID) {
            response(request: $request, user: $user) {
                id
                text
            }
        }
    '''
    result = chatql.schema.execute(
                query,
                context={'engine': engine},
                variables={'request': request, 'user': user_id})

    if result.errors is not None:
        app.logger.error(result.errors)
        abort(500)
    return result.data['response']['text']


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

    user_id = _get_user(**{"user_id": event.source.user_id})
    response = _generate_response(event.message.text, user_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
