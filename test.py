# app.py
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi('aHmpfQGEB7ncEBBPbaFBtZ6rbljmwXgByvCf5/fXIT2eVzsvZ59VhQNpzqfvQpjieram9XSkJU66xTiOrHL6NsdNsDEgeVnNR5ZK2lGmRw4L8Wan3yZQZDUCTgVaOJkJ/9OBXO9E3ROmD5oSdyShzwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('3c3470405b469a2ebdaf5ceb1547c327')

@app.route("/callback", methods=['POST'])
def callback():
    # 確認 Signature
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 處理收到的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 回傳一樣的文字（Echo bot）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

if __name__ == "__main__":
    app.run(port=8000)
