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
        line_user_id = [os.environ.get("USER_ID1"), os.environ.get("USER_ID2"), os.environ.get("USER_ID3")]
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
    if yesterday_data is None:
        print("[錯誤] 無法找到昨天的資料，無法進行比較")
        return None
    elif today_data['date'] == yesterday_data['date']:
        print("[錯誤] 日期與昨天相同，無法比較")
        return None
    else:
        data1 = f"{today_data['taiex']:,}"
        data1_1 = format_diff(today_data['taiex'], yesterday_data['taiex'])
        data2 = f"{today_data['fut_total']:,}"
        data2_1 = format_diff(today_data['fut_total'], yesterday_data['fut_total'])
        data3 = f"{today_data['opt_taiex']:,}"
        data3_1 = format_diff(today_data['opt_taiex'], yesterday_data['opt_taiex'])
        data4 = f"{today_data['opt_total']:,}"
        data4_1 = format_diff(today_data['opt_total'], yesterday_data['opt_total'])
        data5 = f"{today_data['large_5']:,}"
        data5_1 = format_diff(today_data['large_5'], yesterday_data['large_5'])
        data6 = f"{today_data['large_10']:,}"
        data6_1 = format_diff(today_data['large_10'], yesterday_data['large_10'])
        data7 = f"{today_data['small_ratio']}"
        data7_1 = f"{yesterday_data['small_ratio']}"
        data8 = f"{today_data['mini_ratio']}"
        data8_1 = f"{yesterday_data['mini_ratio']}"
        print(
            f"{today_data['date']}\n"
            f"外資大台期貨未平倉口數：{data1} {data1_1} 口\n"
            f"外資期貨總計未平倉口數：{data2} {data2_1} 口\n"
            f"外資台指選擇權未平倉口數：{data3} {data3_1} 口\n"
            f"外資選擇權總計未平倉口數：{data4} {data4_1} 口\n"
            f"前五大台指期貨未平倉口數：{data5} {data5_1} 口\n"
            f"前十大台指期貨未平倉口數：{data6} {data6_1} 口\n"
            f"小台散戶多空比{data7} {data7_1} %\n"
            f"微台散戶多空比{data8} {data8_1} %\n"
        )

        with open('flex_template.json', 'r', encoding='utf-8') as file:
            bubble_dict = json.load(file)
        bubble_dict['body']['contents'][0]['text'] = today_data['date']
        bubble_dict['body']['contents'][3]['contents'][0]['contents'][1]['text'] = data1
        bubble_dict['body']['contents'][3]['contents'][0]['contents'][2]['text'] = data1_1
        bubble_dict['body']['contents'][3]['contents'][0]['contents'][2]['color'] = "#00AA00" if data1_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][1]['contents'][1]['text'] = data2
        bubble_dict['body']['contents'][3]['contents'][1]['contents'][2]['text'] = data2_1
        bubble_dict['body']['contents'][3]['contents'][1]['contents'][2]['color'] = "#00AA00" if data2_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][3]['contents'][1]['text'] = data3
        bubble_dict['body']['contents'][3]['contents'][3]['contents'][2]['text'] = data3_1
        bubble_dict['body']['contents'][3]['contents'][3]['contents'][2]['color'] = "#00AA00" if data3_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][4]['contents'][1]['text'] = data4
        bubble_dict['body']['contents'][3]['contents'][4]['contents'][2]['text'] = data4_1
        bubble_dict['body']['contents'][3]['contents'][4]['contents'][2]['color'] = "#00AA00" if data4_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][6]['contents'][1]['text'] = data5
        bubble_dict['body']['contents'][3]['contents'][6]['contents'][2]['text'] = data5_1
        bubble_dict['body']['contents'][3]['contents'][6]['contents'][2]['color'] = "#00AA00" if data5_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][7]['contents'][1]['text'] = data6
        bubble_dict['body']['contents'][3]['contents'][7]['contents'][2]['text'] = data6_1
        bubble_dict['body']['contents'][3]['contents'][7]['contents'][2]['color'] = "#00AA00" if data6_1[1] == "-" else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][11]['contents'][1]['text'] = data7
        bubble_dict['body']['contents'][3]['contents'][11]['contents'][2]['text'] = data7_1
        bubble_dict['body']['contents'][3]['contents'][11]['contents'][2]['color'] = "#00AA00" if float(data7) < float(data7_1) else "#FF5555"
        bubble_dict['body']['contents'][3]['contents'][12]['contents'][1]['text'] = data8
        bubble_dict['body']['contents'][3]['contents'][12]['contents'][2]['text'] = data8_1
        bubble_dict['body']['contents'][3]['contents'][12]['contents'][2]['color'] = "#00AA00"  if float(data8) < float(data8_1) else "#FF5555"

        flex_msg = FlexMessage.from_dict({
            "type": "flex",
            "altText": "股市資訊",
            "contents": bubble_dict
        })
    return flex_msg

def fetch_total_oi_from_daily_report(query_date, commodity_id):
    try:
        url = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            url,
            fields={
                'queryType': 2,
                'marketCode': 0,
                'commodity_id': commodity_id,
                'queryDate': query_date
            }
        )
        soup = BeautifulSoup(response.data, 'html.parser')
        tables = soup.find_all('table')
        df = pd.read_html(StringIO(str(tables)))[0]
        total_oi_str = df.iloc[-1, 12]  # OI 在第13欄
        total_oi = int(str(total_oi_str).replace(',', ''))
        return total_oi
    except Exception as e:
        print(f"[錯誤] 抓取每日報表 {commodity_id} 失敗：{e}")
        return None

def fetch_legal_total_oi(query_date, commodity_id):
    try:
        url = "https://www.taifex.com.tw/cht/3/futContractsDate"
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            url,
            fields={
                'queryType': 1,
                'doQuery': 1,
                'commodityId': commodity_id,
                'queryDate': query_date
            }
        )
        soup = BeautifulSoup(response.data, 'html.parser')
        tables = soup.find_all('table')
        df = pd.read_html(StringIO(str(tables)))[0]

        for i in range(len(df)):
            if df.iloc[i, 1].strip() == "期貨合計":
                oi_str = df.iloc[i, 13]
                legal_oi = int(str(oi_str).replace(',', ''))
                return legal_oi

        print(f"[警告] 未找到 {commodity_id} 的期貨合計資料")
        return None
    except Exception as e:
        print(f"[錯誤] 抓取法人持倉 {commodity_id} 失敗：{e}")
        return None

def fetch_retail_long_short_ratio(query_date):
    # 抓資料
    small_total_oi = fetch_total_oi_from_daily_report(query_date, "MTX")
    mini_total_oi = fetch_total_oi_from_daily_report(query_date, "TMF")
    small_legal_oi = fetch_legal_total_oi(query_date, "MXF")
    mini_legal_oi = fetch_legal_total_oi(query_date, "TMF")

    # 計算與輸出
    if small_total_oi and small_legal_oi:
        small_ratio = round(-100 * small_legal_oi / small_total_oi, 2)
    else:
        print("[錯誤] 小台資料不足，無法計算")
        small_ratio = None

    if mini_total_oi and mini_legal_oi:
        mini_ratio = round(-100 * mini_legal_oi / mini_total_oi, 2)
    else:
        print("[錯誤] 微台資料不足，無法計算")
        mini_ratio = None

    return small_ratio, mini_ratio

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
        print(data_frame)
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

if __name__ == '__main__':
    # 載入環境變數
    load_dotenv()

    # 取得今天日期
    today_str = date.today().strftime('%Y/%m/%d')
    # today_str = "2025/07/25" # 測試用

    taiex_oi, fut_total_oi = retry_fetch(fetch_taiex_futures_data, args=(today_str,))
    opt_oi, opt_total_oi = retry_fetch(fetch_option_data, args=(today_str,))
    large_5_oi, large_10_oi = retry_fetch(fetch_large_future_data, args=(today_str,))
    small_ratio, mini_ratio = retry_fetch(fetch_retail_long_short_ratio, args=(today_str,))

    today_data = {
        'date': today_str,
        'taiex': taiex_oi,
        'fut_total': fut_total_oi,
        'opt_taiex': opt_oi,
        'opt_total': opt_total_oi,
        'large_5': large_5_oi,
        'large_10': large_10_oi,
        'small_ratio': small_ratio,
        'mini_ratio': mini_ratio
    }

    # 載入昨天的資料
    yesterday_data = load_previous_data()

    flex_message = generate_flex_message_dict(today_data, yesterday_data)

    if flex_message:
        send_line_message(flex_message)
    # 儲存今天資料，給明天比對用
    save_today_data(today_data)