"""測試抓取日盤振幅 - 驗證能正確取得指定日期的振幅"""
import urllib3
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO


def fetch_daily_amplitude(query_date, commodity_id="TX"):
    """抓取指定日期的期貨日盤振幅（最高價 - 最低價）"""
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

    # 表格：契約、到期月份、開盤、最高、最低、最後...
    high_val = df.iloc[0, 3]  # 最高
    low_val = df.iloc[0, 4]   # 最低

    high = int(float(str(high_val).replace(",", "").strip()))
    low = int(float(str(low_val).replace(",", "").strip()))
    print("high", high)
    print("low", low)
    print("high - low", high - low)
    return high - low


if __name__ == "__main__":
    query_date = "2026/03/13"
    commodity_id = "TX"
    print(f"抓取 {query_date} 的 {commodity_id} 日盤振幅...")
    amplitude = fetch_daily_amplitude(query_date, commodity_id)
    print(f"當日振幅（最高 - 最低）= {amplitude} 點")
