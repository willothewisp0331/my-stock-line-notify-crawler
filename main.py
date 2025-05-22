import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from datetime import date, timedelta
from io import StringIO
import os
import json
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, PushMessageRequest
from linebot.v3.messaging.models import TextMessage
import re

DATA_FILE = 'daily_open_interest.json'
user_lin = "U2e7ddaa0d777d91a3496d7336da8edec"

def send_line_message(message_text):
    access_token = os.environ.get("LINE_TOKEN")
    line_user_id = os.environ.get("USER_ID")

    configuration = Configuration(access_token=access_token)
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.push_message(
            PushMessageRequest(
                to=line_user_id,
                messages=[TextMessage(text=message_text)]
            )
        )

def fetch_taiex_futures_data(query_date):
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
    foreign_total_open_interest = int(data_frame.iloc[71, 13])
    taiex_open_interest = int(data_frame.iloc[2, 13])
    return taiex_open_interest, foreign_total_open_interest

def fetch_option_data(query_date):
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
    foreign_total_option_open_interest = int(data_frame.iloc[17, 13])
    option_open_interest = int(data_frame.iloc[2, 13])
    return option_open_interest, foreign_total_option_open_interest

def clean_data_to_int(data):
    data_clean = re.sub(r"\s*\(.*?\)", "", data)
    data_clean = data_clean.replace(",", "")
    return int(data_clean)

def fetch_large_future_data(query_date):
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

def load_previous_data():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_today_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def generate_comparison(today_data, yesterday_data):
    def format_diff(current, prev):
        diff = current - prev
        sign = "+" if diff >= 0 else ""
        return f"{current:,}（{sign}{diff:,}）"

    return (
        f"{today_data['date']}\n"
        f"外資大台期貨未平倉口數：{format_diff(today_data['taiex'], yesterday_data['taiex'])} 口\n"
        f"外資期貨總計未平倉口數：{format_diff(today_data['fut_total'], yesterday_data['fut_total'])} 口\n"
        f"外資台指選擇權未平倉口數：{format_diff(today_data['opt_taiex'], yesterday_data['opt_taiex'])} 口\n"
        f"外資選擇權總計未平倉口數：{format_diff(today_data['opt_total'], yesterday_data['opt_total'])} 口\n"
        f"前五大台指期貨未平倉口數：{format_diff(today_data['large_5'], yesterday_data['large_5'])} 口\n"
        f"前十大台指期貨未平倉口數：{format_diff(today_data['large_10'], yesterday_data['large_10'])} 口"
    )

if __name__ == '__main__':
    # today_str = date.today().strftime('%Y/%m/%d')
    today_str = "2025/05/16"
    taiex_oi, fut_total_oi = fetch_taiex_futures_data(today_str)
    opt_oi, opt_total_oi = fetch_option_data(today_str)
    large_5_oi, large_10_oi = fetch_large_future_data(today_str)

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

    # 有昨天資料就做比較，沒有就顯示今天的數據
    if yesterday_data:
        message_text = generate_comparison(today_data, yesterday_data)
    else:
        message_text = (
            f"{today_data['date']}\n"
            f"外資台指期貨未平倉口數：{today_data['taiex']:,} 口\n"
            f"外資期貨總計未平倉口數：{today_data['fut_total']:,} 口\n"
            f"外資台指選擇權未平倉口數：{today_data['opt_taiex']:,} 口\n"
            f"外資選擇權總計未平倉口數：{today_data['opt_total']:,} 口\n"
            f"前五大台指期貨未平倉口數：{today_data['large_5']:,} 口\n"
            f"前十大台指期貨未平倉口數：{today_data['large_10']:,} 口\n"
        )

    print(message_text)
    # send_line_message(message_text)  # 你要開就取消註解

    # 儲存今天資料，給明天比對用
    save_today_data(today_data)