import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from datetime import date, timedelta
from io import StringIO
import os
import json
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, PushMessageRequest
from linebot.v3.messaging.models import FlexMessage, TextMessage, Message
import re
from dotenv import load_dotenv
import time

DATA_FILE = 'daily_open_interest.json'

def send_line_message(flex_msg):
    try:
        access_token = os.environ.get("LINE_TOKEN")
        line_user_id = [os.environ.get("USER_ID1"), os.environ.get("USER_ID2")]
        if not access_token:
            print("環境變數未設定，請確認 bat 檔或 .env 檔是否正確！")
        configuration = Configuration(access_token=access_token)
        with ApiClient(configuration) as api_client:
            for id in line_user_id:
                MessagingApi(api_client).push_message(
                    PushMessageRequest(to=id, messages=[flex_msg])
                )
        print("已成功傳送Line訊息")
    except Exception as e:
        print(f"[錯誤] 發送 LINE 訊息失敗：{e}")


def generate_flex_message_dict(today_data, yesterday_data):
    def format_diff(current, prev):
        diff = current - prev
        sign = "+" if diff >= 0 else ""
        return f"({sign}{diff:,}）"

    if today_data['date'] == yesterday_data['date']:
        print("[錯誤] 日期與昨天相同，無法比較")
        return None
    else:
        data1 = f"{today_data['taiex']:,}"
        data2 = f"{today_data['fut_total']:,}"
        data3 = f"{today_data['opt_taiex']:,}"
        data4 = f"{today_data['opt_total']:,}"
        data5 = f"{today_data['large_5']:,}"
        data6 = f"{today_data['large_10']:,}"
        print(
            f"{today_data['date']}\n"
            f"外資大台期貨未平倉口數：{data1} {format_diff(today_data['taiex'], yesterday_data['taiex'])} 口\n"
            f"外資期貨總計未平倉口數：{data2} {format_diff(today_data['fut_total'], yesterday_data['fut_total'])} 口\n"
            f"外資台指選擇權未平倉口數：{data3} {format_diff(today_data['opt_taiex'], yesterday_data['opt_taiex'])} 口\n"
            f"外資選擇權總計未平倉口數：{data4} {format_diff(today_data['opt_total'], yesterday_data['opt_total'])} 口\n"
            f"前五大台指期貨未平倉口數：{data5} {format_diff(today_data['large_5'], yesterday_data['large_5'])} 口\n"
            f"前十大台指期貨未平倉口數：{data6} {format_diff(today_data['large_10'], yesterday_data['large_10'])} 口"
        )
        bubble_dict = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": today_data['date'],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#0B6E99"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "類型",
                                "size": "md",
                                "color": "#555555",
                                "flex": 4
                            },
                            {
                                "type": "text",
                                "text": "未平倉口數",
                                "size": "xs",
                                "color": "#555555",
                                "flex": 3
                            },
                            {
                                "type": "text",
                                "text": "與前值相比",
                                "size": "xs",
                                "color": "#555555",
                                "flex": 0
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "外資台指期貨",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data1,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['taiex'], yesterday_data['taiex']),
                                        "size": "sm",
                                        "color": "#FF5555",
                                        "flex": 2,
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
                                        "text": "外資期貨總計",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data2,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['fut_total'], yesterday_data['fut_total']),
                                        "size": "sm",
                                        "color": "#FF5555",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "separator"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "外資選擇權",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data3,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['opt_taiex'], today_data['opt_taiex']),
                                        "size": "sm",
                                        "color": "#00AA00",
                                        "flex": 2,
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
                                        "text": "外資選擇權總計",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data4,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['opt_total'], yesterday_data['opt_total']),
                                        "size": "sm",
                                        "color": "#00AA00",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "separator"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "前五大台指期",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data5,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['large_5'], yesterday_data['large_5']),
                                        "size": "sm",
                                        "color": "#FF5555",
                                        "flex": 2,
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
                                        "text": "前十大台指期",
                                        "size": "sm",
                                        "color": "#555555",
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": data6,
                                        "size": "sm",
                                        "color": "#111111",
                                        "flex": 2,
                                        "align": "end"
                                    },
                                    {
                                        "type": "text",
                                        "text": format_diff(today_data['large_10'], yesterday_data['large_10']),
                                        "size": "sm",
                                        "color": "#FF5555",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "separator"
                            }
                        ]
                    }
                ]
            }
        }
        flex_msg = FlexMessage.from_dict({
            "type": "flex",
            "altText": "股市資訊",
            "contents": bubble_dict
        })
    return flex_msg


def fetch_taiex_futures_data(query_date):
    try:
        url = "https://www.taifex.com.tw/cht/3/futContractsDate"
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            url,
            fields={
                'queryType': 1,
                'doQuery': 1,
                'queryDate': query_date
            }
        )
        soup = BeautifulSoup(response.data, 'html.parser')
        table_html = soup.find_all('table')
        data_frame = pd.read_html(StringIO(str(table_html)))[0]
        for i in range(len(data_frame)):
            if data_frame.iloc[i, 1] == "期貨 小計" and data_frame.iloc[i, 2] == "外資":
                foreign_total_open_interest = int(data_frame.iloc[i, 13])
            if data_frame.iloc[i, 1] == "臺股期貨" and data_frame.iloc[i, 2] == "外資":
                taiex_open_interest = int(data_frame.iloc[i, 13])
        return taiex_open_interest, foreign_total_open_interest
    except Exception as e:
        print(f"[錯誤] 抓取資料失敗：{e}")
        return None


def fetch_option_data(query_date):
    try:
        url = "https://www.taifex.com.tw/cht/3/optContractsDate"
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            url,
            fields={
                'queryType': 1,
                'doQuery': 1,
                'queryDate': query_date
            }
        )
        soup = BeautifulSoup(response.data, 'html.parser')
        table_html = soup.find_all('table')
        data_frame = pd.read_html(StringIO(str(table_html)))[0]
        for i in range(len(data_frame)):
            if data_frame.iloc[i, 1] == "選擇權 小計" and data_frame.iloc[i, 2] == "外資":
                foreign_total_option_open_interest = int(data_frame.iloc[i, 13])
            if data_frame.iloc[i, 1] == "臺指選擇權" and data_frame.iloc[i, 2] == "外資":
                option_open_interest = int(data_frame.iloc[i, 13])
        return option_open_interest, foreign_total_option_open_interest
    except Exception as e:
        print(f"[錯誤] 抓取資料失敗：{e}")
        return None


def clean_data_to_int(data):
    data_clean = re.sub(r"\s*\(.*?\)", "", data)
    data_clean = data_clean.replace(",", "")
    return int(data_clean)


def fetch_large_future_data(query_date):
    try:
        url = "https://www.taifex.com.tw/cht/3/largeTraderFutQry"
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            url,
            fields={
                'contractId': 'TX',
                'queryDate': query_date
            }
        )
        soup = BeautifulSoup(response.data, 'html.parser')
        table_html = soup.find_all('table')
        data_frame = pd.read_html(StringIO(str(table_html)))[0]
        large_open_interest = clean_data_to_int(data_frame.iloc[1, 2]) - clean_data_to_int(data_frame.iloc[1, 6])
        large_total_open_interest = clean_data_to_int(data_frame.iloc[1, 4]) - clean_data_to_int(data_frame.iloc[1, 8])
        return large_open_interest, large_total_open_interest
    except Exception as e:
        print(f"[錯誤] 抓取資料失敗：{e}")
        return None


def load_previous_data():
    try:
        if not os.path.exists(DATA_FILE):
            return None
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[錯誤] 載入昨天資料失敗：{e}")
        return None


def save_today_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[錯誤] 儲存今天資料失敗：{e}")

def retry_fetch(func, args=(), kwargs={}, max_retries=4, retry_delay=15):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"第 {attempt} 次嘗試執行 {func.__name__}...")
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[警告] {func.__name__} 第 {attempt} 次失敗：{e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"[錯誤] 連續 {max_retries} 次失敗：{func.__name__} 無法完成。") from e


#
# def generate_comparison(today_data, yesterday_data):
#     def format_diff(current, prev):
#         diff = current - prev
#         sign = "+" if diff >= 0 else ""
#         return f"{current:,}（{sign}{diff:,}）"
#     if today_data['date'] == yesterday_data['date']:
#         return "[錯誤] 日期與昨天相同，無法比較"
#     else:
#         return (
#             f"{today_data['date']}\n"
#             f"外資大台期貨未平倉口數：{format_diff(today_data['taiex'], yesterday_data['taiex'])} 口\n"
#             f"外資期貨總計未平倉口數：{format_diff(today_data['fut_total'], yesterday_data['fut_total'])} 口\n"
#             f"外資台指選擇權未平倉口數：{format_diff(today_data['opt_taiex'], yesterday_data['opt_taiex'])} 口\n"
#             f"外資選擇權總計未平倉口數：{format_diff(today_data['opt_total'], yesterday_data['opt_total'])} 口\n"
#             f"前五大台指期貨未平倉口數：{format_diff(today_data['large_5'], yesterday_data['large_5'])} 口\n"
#             f"前十大台指期貨未平倉口數：{format_diff(today_data['large_10'], yesterday_data['large_10'])} 口"
#         )

if __name__ == '__main__':
    # 載入環境變數
    load_dotenv()

    # 取得今天日期
    today_str = date.today().strftime('%Y/%m/%d')
    taiex_oi, fut_total_oi = retry_fetch(fetch_taiex_futures_data, args=(today_str,))
    opt_oi, opt_total_oi = retry_fetch(fetch_option_data, args=(today_str,))
    large_5_oi, large_10_oi = retry_fetch(fetch_large_future_data, args=(today_str,))

    today_data = {
        'date': today_str,
        'taiex': taiex_oi,
        'fut_total': fut_total_oi,
        'opt_taiex': opt_oi,
        'opt_total': opt_total_oi,
        'large_5': large_5_oi,
        'large_10': large_10_oi
    }

    # 載入昨天的資料
    yesterday_data = load_previous_data()

    flex_message = generate_flex_message_dict(today_data, yesterday_data)

    if flex_message:
        send_line_message(flex_message)
    # 儲存今天資料，給明天比對用
    save_today_data(today_data)