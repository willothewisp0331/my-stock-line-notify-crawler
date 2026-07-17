# 部署 LINE Webhook Server 到 Render.com

## 前置條件

1. 有 [Render.com](https://render.com) 帳號
2. 專案已推上 GitHub（public 或 private 皆可）
3. 有 LINE Channel 的 `LINE_SECRET` 和 `LINE_TOKEN`

---

## 步驟一：推送程式碼到 GitHub

```bash
git add webhook_server.py users.json render.yaml requirements.txt
git commit -m "feat: add LINE webhook server for auto user ID collection"
git push origin main
```

---

## 步驟二：在 Render.com 建立 Web Service

1. 登入 [Render Dashboard](https://dashboard.render.com)
2. 點選 **New** → **Web Service**
3. 連接你的 GitHub repo（`my-stock-line-notify-crawler`）
4. 設定：
   - **Name**: `line-webhook-server`（或任意名稱）
   - **Region**: Singapore（離台灣最近）
   - **Branch**: `main`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webhook_server:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free（免費方案即可）

5. 在 **Environment** 頁面加入環境變數：
   - `LINE_SECRET` = 你的 LINE Channel Secret
   - `LINE_TOKEN` = 你的 LINE Channel Access Token

6. 點選 **Create Web Service**

部署完成後你會得到一個 URL，例如：
```
https://line-webhook-server-xxxx.onrender.com
```

---

## 步驟三：設定 LINE Webhook URL

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 進入你的 Channel → **Messaging API** 頁籤
3. 在 **Webhook URL** 欄位填入：
   ```
   https://line-webhook-server-xxxx.onrender.com/callback
   ```
4. 點選 **Verify** 確認連線成功（應回傳 200）
5. 確保 **Use webhook** 開關為開啟狀態

---

## 步驟四：測試

1. 用手機加你的 LINE Bot 好友
2. 檢查 Render 的 Logs 應看到：
   ```
   [EVENT] 新粉絲加入: Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   [INFO] 新增用戶: Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (未知)
   ```
3. 瀏覽 `https://你的URL/users` 確認用戶已被記錄

---

## 查看已收集的用戶

瀏覽器打開：
```
https://line-webhook-server-xxxx.onrender.com/users
```

會回傳 JSON 格式的用戶列表。

---

## 讓 main.py 也讀取 users.json

未來你可以修改 `main.py` 的 `send_line_message` 函數，改為從 `users.json` 讀取用戶列表：

```python
def get_user_ids():
    with open("users.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return [u["user_id"] for u in data["users"]]
```

這樣就不用再手動維護 `.env` 裡的 USER_ID 了。

---

## 注意事項

- **Render 免費方案**：閒置 15 分鐘會休眠，收到請求會冷啟動（約 30 秒）。LINE 的 webhook 有 timeout 限制，但 follow 事件通常不影響。
- **users.json 持久化**：Render 免費方案的磁碟不持久化（重新部署會重置）。如果擔心資料遺失，可以改用外部儲存（如 GitHub API 寫回 repo、或用免費的 MongoDB Atlas）。
- **安全性**：`/users` 端點目前無認證，建議部署後加上簡單的 token 驗證，或只在需要時啟用。
