"""
初始化 20 日振幅資料，寫入 daily_open_interest.json。
可先寫死 20 個交易日日期，執行後會抓取各日振幅並寫入 amplitude_history。
之後 main.py 會自動以 FIFO 方式維護這 20 筆資料。
"""
import json
import os
import sys
import urllib3
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO


def fetch_daily_amplitude(query_date, commodity_id="TX"):
    """抓取指定日期的期貨日盤振幅（不依賴 main）"""
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
    high_val = df.iloc[0, 3]
    low_val = df.iloc[0, 4]
    high = int(float(str(high_val).replace(",", "").strip()))
    low = int(float(str(low_val).replace(",", "").strip()))
    return high - low


# 可手動修改的 20 個交易日日期（依時間由舊到新）
INITIAL_AMPLITUDE_DATES = [
    "2026/2/3",
    "2026/2/4",
    "2026/2/5",
    "2026/2/6",
    "2026/2/9",
    "2026/2/10",
    "2026/2/11",
    "2026/2/23",
    "2026/2/24",
    "2026/2/25",
    "2026/2/26",
    "2026/3/2",
    "2026/3/3",
    "2026/3/4",
    "2026/3/5",
    "2026/3/6",
    "2026/3/9",
    "2026/3/10",
    "2026/3/11",
    "2026/3/12"
]

DATA_FILE = "daily_open_interest.json"


def main():
    amplitude_history = []
    for d in INITIAL_AMPLITUDE_DATES:
        print(f"抓取 {d} 振幅...", end=" ")
        try:
            amp = fetch_daily_amplitude(d)
            amplitude_history.append({"date": d, "amplitude": amp})
            print(f"{amp} 點")
        except Exception as e:
            print(f"失敗：{e}")
            sys.exit(1)

    # 與既有 daily_open_interest 合併（若存在）
    existing = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing["amplitude_history"] = amplitude_history
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n已寫入 {DATA_FILE}，共 {len(amplitude_history)} 筆振幅資料")


if __name__ == "__main__":
    main()
