from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, PushMessageRequest
from linebot.v3.messaging.models.flex_message import FlexMessage
import os

access_token = os.environ.get("LINE_TOKEN")
user_id = os.environ.get("USER_ID1")
print(access_token)
print(user_id)

# 組成 Flex bubble dict
bubble_dict = {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "股市資訊",
        "weight": "bold",
        "color": "#1DB446",
        "size": "sm"
      },
      {
        "type": "separator",
        "margin": "sm"
      },
      {
        "type": "box",
        "layout": "vertical",
        "margin": "xxl",
        "spacing": "sm",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "台指期貨",
                "size": "sm",
                "color": "#555555",
                "flex": 0
              },
              {
                "type": "text",
                "text": "-40656口",
                "size": "sm",
                "color": "#111111",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "期貨商品總計",
                "size": "sm",
                "color": "#555555",
                "flex": 0
              },
              {
                "type": "text",
                "text": "-313639口",
                "size": "sm",
                "color": "#111111",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "vertical",
            "margin": "xxl",
            "spacing": "sm",
            "contents": [
              {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                  {
                    "type": "text",
                    "text": "台指期貨",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0
                  },
                  {
                    "type": "text",
                    "text": "-40656口",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                  }
                ]
              },
              {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                  {
                    "type": "text",
                    "text": "期貨商品總計",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0
                  },
                  {
                    "type": "text",
                    "text": "-313639口",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                  }
                ]
              }
            ]
          },
          {
            "type": "box",
            "layout": "vertical",
            "margin": "xxl",
            "spacing": "sm",
            "contents": [
              {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                  {
                    "type": "text",
                    "text": "台指期貨",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0
                  },
                  {
                    "type": "text",
                    "text": "-40656口",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                  }
                ]
              },
              {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                  {
                    "type": "text",
                    "text": "期貨商品總計",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0
                  },
                  {
                    "type": "text",
                    "text": "-313639口",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "type": "separator",
        "margin": "xxl"
      }
    ]
  },
  "styles": {
    "footer": {
      "separator": True
    }
  }
}

# 用 FlexMessage.from_dict 包起來
flex_msg = FlexMessage.from_dict({
    "type": "flex",
    "altText": "股市資訊",
    "contents": bubble_dict
})

# 發送
configuration = Configuration(access_token=access_token)
with ApiClient(configuration) as api_client:
    MessagingApi(api_client).push_message(
        PushMessageRequest(to=user_id, messages=[flex_msg])
    )
