"""
LINE Webhook Server（本機版）
用法：
  1. pip install flask python-dotenv
  2. python webhook_server.py
  3. 另開終端執行 ngrok http 5000
  4. 把 ngrok 給的 https URL + /callback 貼到 LINE Developers Console 的 Webhook URL
  5. 請新用戶傳訊息給 Bot，user ID 會自動存入 users.json
  6. 收完後 Ctrl+C 關掉即可
"""

import json
import os
import hashlib
import hmac
import base64
from datetime import datetime

from flask import Flask, request, abort, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_SECRET")
USERS_FILE = "users.json"


def verify_signature(body, signature):
    """驗證 LINE 的 webhook 簽章"""
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


def load_users():
    if not os.path.exists(USERS_FILE):
        return {"users": []}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_user(user_id):
    """新增用戶到 users.json（不重複）"""
    data = load_users()
    existing_ids = [u["user_id"] for u in data["users"]]

    if user_id in existing_ids:
        print(f"[略過] 用戶已存在: {user_id}")
        return False

    new_user = {
        "user_id": user_id,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["users"].append(new_user)
    save_users(data)
    print(f"[新增] ✅ 新用戶: {user_id}")
    print(f"[目前] 共 {len(data['users'])} 位用戶")
    return True


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook 端點"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    # 驗證簽章
    if not LINE_CHANNEL_SECRET:
        print("[錯誤] LINE_SECRET 未設定，請檢查 .env")
        abort(500)

    if not verify_signature(body, signature):
        print("[錯誤] 簽章驗證失敗")
        abort(403)

    # 解析事件
    events = json.loads(body).get("events", [])

    for event in events:
        event_type = event.get("type")
        user_id = event.get("source", {}).get("userId")

        if not user_id:
            continue

        if event_type == "follow":
            print(f"[事件] 加好友: {user_id}")
            add_user(user_id)
        elif event_type == "message":
            print(f"[事件] 收到訊息來自: {user_id}")
            add_user(user_id)

    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    """查看目前用戶列表"""
    data = load_users()
    count = len(data["users"])
    user_list = "\n".join(
        [f"  {i+1}. {u['user_id']} ({u.get('added_at', '?')})" for i, u in enumerate(data["users"])]
    )
    return f"<pre>LINE Webhook Server 運行中\n\n目前共 {count} 位用戶:\n{user_list}</pre>"


if __name__ == "__main__":
    print("=" * 50)
    print(" LINE Webhook Server（本機版）")
    print("=" * 50)
    print()
    print("步驟：")
    print("  1. 另開終端執行: ngrok http 5000")
    print("  2. 複製 ngrok 的 https URL")
    print("  3. 到 LINE Developers Console 貼上: https://xxx.ngrok-free.app/callback")
    print("  4. 請用戶傳訊息給 Bot")
    print("  5. 收完後 Ctrl+C 關閉")
    print()
    print(f"目前已有 {len(load_users()['users'])} 位用戶")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
