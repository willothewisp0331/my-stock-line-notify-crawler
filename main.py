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
import traceback

DATA_FILE = 'daily_open_interest.json'
AMPLITUDE_HISTORY_SIZE = 20

def send_line_message(flex_msg):
    try:
        access_token = os.environ.get("LINE_TOKEN")
        line_user_id = [os.environ.get("USER_ID1")]
        
        # line_user_id = [os.environ.get("USER_ID1"), os.environ.get("USER_ID2"), os.environ.get("USER_ID3")]
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
            f"振幅統計(近20日)：\n"
            f"  最大值：{today_data.get('amplitude_max', '-')}\n"
            f"  最小值：{today_data.get('amplitude_min', '-')}\n"
            f"  平均值：{today_data.get('amplitude_avg', '-')}\n"
            f"  今日振幅：{today_data.get('amplitude_today', '-')}\n"
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
        # 振幅區（波動度評估）：contents[16-19] 為最大/最小/平均/今日振幅
        amp_max = str(today_data.get('amplitude_max', '-'))
        amp_min = str(today_data.get('amplitude_min', '-'))
        amp_avg = str(today_data.get('amplitude_avg', '-'))
        amp_today = str(today_data.get('amplitude_today', '-'))
        bubble_dict['body']['contents'][3]['contents'][16]['contents'][1]['text'] = amp_max
        bubble_dict['body']['contents'][3]['contents'][17]['contents'][1]['text'] = amp_min
        bubble_dict['body']['contents'][3]['contents'][18]['contents'][1]['text'] = amp_avg
        bubble_dict['body']['contents'][3]['contents'][19]['contents'][1]['text'] = amp_today
        bubble_dict['body']['contents'][3]['contents'][19]['contents'][1]['color'] = "#00AA00"  if float(amp_today) < float(amp_avg) else "#FF5555"

        flex_msg = FlexMessage.from_dict({
            "type": "flex",
            "altText": "股市資訊",
            "contents": bubble_dict
        })
    return flex_msg

def fetch_daily_amplitude(query_date, commodity_id="TX"):
    """
    抓取指定日期的期貨日盤振幅（最高價 - 最低價）。
    資料來源：期交所期貨每日交易行情查詢 futDailyMarketReport
    預設抓取大台(TX)近月契約的日盤振幅。
    """
    try:
        url = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
        http = urllib3.PoolManager()
        response = http.request(
            "POST",
            url,
            fields={
                "queryType": 2,
                "marketCode": 0,
                "commodity_id": commodity_id,
                "queryDate": query_date,
            },
        )
        soup = BeautifulSoup(response.data, "html.parser")
        tables = soup.find_all("table")
        df = pd.read_html(StringIO(str(tables)))[0]

        # 表格結構：契約、到期月份、開盤、最高、最低、最後... 最高通常在欄 3，最低在欄 4
        # 近月契約為第一列資料（索引 0），最後一列為合計
        high_val = df.iloc[0, 3]  # 最高
        low_val = df.iloc[0, 4]   # 最低

        # 期貨價格可能為小數，需先轉 float 再取整
        high = int(float(str(high_val).replace(",", "").strip()))
        low = int(float(str(low_val).replace(",", "").strip()))
        amplitude = high - low
        return amplitude
    except Exception as e:
        print(f"[錯誤] 抓取日盤振幅 {commodity_id} 失敗：{e}")
        raise


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
        total_oi = clean_data_to_int(total_oi_str)
        return total_oi
    except Exception as e:
        print(f"[錯誤] 抓取每日報表 {commodity_id} 失敗：{e}")
        raise

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
                legal_oi = clean_data_to_int(df.iloc[i, 13])
                return legal_oi

        print(f"[警告] 未找到 {commodity_id} 的期貨合計資料")
        return None
    except Exception as e:
        print(f"[錯誤] 抓取法人持倉 {commodity_id} 失敗：{e}")
        raise

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
        raise ValueError("小台資料不足，無法計算")

    if mini_total_oi and mini_legal_oi:
        mini_ratio = round(-100 * mini_legal_oi / mini_total_oi, 2)
    else:
        print("[錯誤] 微台資料不足，無法計算")
        raise ValueError("微台資料不足，無法計算")

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
        # print(data_frame)
        for i in range(len(data_frame)):
            if data_frame.iloc[i, 1] == "期貨 小計" and data_frame.iloc[i, 2] == "外資":
                foreign_total_open_interest = clean_data_to_int(data_frame.iloc[i, 13])
            if data_frame.iloc[i, 1] == "臺股期貨" and data_frame.iloc[i, 2] == "外資":
                taiex_open_interest = clean_data_to_int(data_frame.iloc[i, 13])
        return taiex_open_interest, foreign_total_open_interest
    except Exception as e:
        print(f"[錯誤] 抓取資料失敗：{e}")
        raise

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
                foreign_total_option_open_interest = clean_data_to_int(data_frame.iloc[i, 13])
            if data_frame.iloc[i, 1] == "臺指選擇權" and data_frame.iloc[i, 2] == "外資":
                option_open_interest = clean_data_to_int(data_frame.iloc[i, 13])
        return option_open_interest, foreign_total_option_open_interest
    except Exception as e:
        print(f"[錯誤] 抓取資料失敗：{e}")
        raise

def clean_data_to_int(data):
    # 處理特殊值
    if pd.isna(data) or str(data).strip() in ['-', '', 'nan', 'NaN', 'NAN']:
        raise ValueError(f"資料為空值或無效值: {data}")
    
    data_clean = re.sub(r"\s*\(.*?\)", "", str(data))
    data_clean = data_clean.replace(",", "")
    data_clean = data_clean.strip()
    
    if not data_clean or data_clean == '-':
        raise ValueError(f"清理後的資料為空或無效: {data}")
    
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
        raise

def load_previous_data():
    try:
        if not os.path.exists(DATA_FILE):
            return None
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[錯誤] 載入昨天資料失敗：{e}")
        return None


def get_amplitude_history(loaded_data):
    """從載入的資料取得 amplitude_history，若無則回傳空列表"""
    if loaded_data is None:
        return []
    return loaded_data.get('amplitude_history', [])


def update_amplitude_history(history, new_date, new_amplitude):
    """
    FIFO 更新振幅歷史：若已滿 20 筆則踢除最久一筆，加入新資料。
    history 為 [{"date": "YYYY/MM/DD", "amplitude": int}, ...]，依日期由舊到新排序。
    """
    new_entry = {"date": new_date, "amplitude": new_amplitude}
    updated = list(history)
    if len(updated) >= AMPLITUDE_HISTORY_SIZE:
        updated.pop(0)
    updated.append(new_entry)
    return updated


def compute_amplitude_stats(history):
    """
    計算近 20 日振幅統計：平均、最小、最大、今日振幅。
    若無資料則回傳 None。
    """
    if not history:
        return None
    amplitudes = [h["amplitude"] for h in history]
    return {
        "avg": round(sum(amplitudes) / len(amplitudes), 1),
        "min": min(amplitudes),
        "max": max(amplitudes),
        "today": history[-1]["amplitude"],
    }


def save_today_data(data, amplitude_history=None):
    try:
        to_save = dict(data)
        if amplitude_history is not None:
            to_save["amplitude_history"] = amplitude_history
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[錯誤] 儲存今天資料失敗：{e}")

def retry_fetch(func, args=(), kwargs={}, max_retries=5, retry_delay=30):
    """
    重試機制：執行函數，失敗後等待指定時間再試
    最多嘗試 max_retries 次，即使全部失敗也不會中斷程序
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[LOG] 第 {attempt}/{max_retries} 次嘗試執行 {func.__name__}...")
            result = func(*args, **kwargs)
            print(f"[LOG] {func.__name__} 第 {attempt} 次執行成功")
            return result
        except Exception as e:
            print(f"[錯誤] {func.__name__} 第 {attempt} 次失敗：{e}")
            print(f"[LOG] 詳細錯誤訊息：")
            traceback.print_exc()
            
            if attempt < max_retries:
                print(f"[LOG] 等待 {retry_delay} 秒後再試...")
                time.sleep(retry_delay)
            else:
                print(f"[錯誤] {func.__name__} 連續 {max_retries} 次都失敗，返回 None")
    return None

if __name__ == '__main__':
    # 載入環境變數
    load_dotenv()

    # 取得今天日期
    # today_str = date.today().strftime('%Y/%m/%d')
    today_str = "2026/03/12" # 測試用

    print(f"[LOG] 開始抓取 {today_str} 的資料...")
    
    # 使用重試機制抓取資料（最多重試5次，每次間隔30秒）
    futures_result = retry_fetch(fetch_taiex_futures_data, args=(today_str,))
    option_result = retry_fetch(fetch_option_data, args=(today_str,))
    large_result = retry_fetch(fetch_large_future_data, args=(today_str,))
    ratio_result = retry_fetch(fetch_retail_long_short_ratio, args=(today_str,))
    amplitude_result = retry_fetch(fetch_daily_amplitude, args=(today_str,))

    # 檢查所有資料是否都成功抓取（重試5次後）
    if futures_result is None or option_result is None or large_result is None or ratio_result is None:
        print("[錯誤] 有資料在重試5次後仍無法抓取，無法發送 LINE 訊息")
        print("[錯誤] 已確保資料正確性，終止程式")
        exit(1)

    # 所有資料都成功抓取，解包資料
    taiex_oi, fut_total_oi = futures_result
    opt_oi, opt_total_oi = option_result
    large_5_oi, large_10_oi = large_result
    small_ratio, mini_ratio = ratio_result

    print(f"[LOG] 所有資料抓取成功，準備產生訊息...")

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

    # 振幅：載入歷史、FIFO 更新、計算統計
    yesterday_data = load_previous_data()
    amplitude_history = get_amplitude_history(yesterday_data)
    if amplitude_result is not None:
        amplitude_history = update_amplitude_history(
            amplitude_history, today_str, amplitude_result
        )
        stats = compute_amplitude_stats(amplitude_history)
        if stats:
            today_data["amplitude_avg"] = stats["avg"]
            today_data["amplitude_min"] = stats["min"]
            today_data["amplitude_max"] = stats["max"]
            today_data["amplitude_today"] = stats["today"]
            print(
                f"[振幅] 近20日 avg={stats['avg']} min={stats['min']} max={stats['max']} 今日={stats['today']}"
            )
    else:
        # 振幅抓取失敗時沿用原 history，不加入今日
        print("[警告] 振幅抓取失敗，未更新 amplitude_history")
    print(today_data)

    flex_message = generate_flex_message_dict(today_data, yesterday_data)

    if flex_message:
        print(f"[LOG] 準備發送 LINE 訊息...")
        send_line_message(flex_message)
        print(f"[LOG] LINE 訊息發送成功")
    else:
        print("[錯誤] 無法產生 Flex 訊息，無法發送 LINE 訊息")
        exit(1)
    
    # 儲存今天資料（含 amplitude_history），給明天比對用
    save_today_data(today_data, amplitude_history)
    print(f"[LOG] 程式執行完成")