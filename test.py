import urllib3
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
#
# query_date = "2025/06/05"
# url = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
# http = urllib3.PoolManager()
# response = http.request(
#     'POST',
#     url,
#     fields={
#         'queryType': 2,
#         'marketCode': 0,
#         'commodity_id': "MTX",
#         'queryDate': query_date
#     }
# )
# soup = BeautifulSoup(response.data, 'html.parser')
# table_html = soup.find_all('table')
# data_frame = pd.read_html(StringIO(str(table_html)))[0]
# small_total_oi = data_frame.iloc[-1, 12]
#
# print("__________________")
# response2 = http.request(
#   'POST',
#   url,
#   fields={
#     'queryType': 2,
#     'marketCode': 0,
#     'commodity_id': "TMF",
#     'queryDate': query_date
#   }
# )
# soup2 = BeautifulSoup(response2.data, 'html.parser')
# table_html2 = soup2.find_all('table')
# data_frame2 = pd.read_html(StringIO(str(table_html2)))[0]
# mini_total_oi = data_frame2.iloc[-1, 12]
#
#
# url3 = "https://www.taifex.com.tw/cht/3/futContractsDate"
# http3 = urllib3.PoolManager()
# response3 = http3.request(
#   'POST',
#   url3,
#   fields={
#     'queryType': 1,
#     'doQuery': 1,
#     'commodityId': "MXF",
#     'queryDate': query_date
#   }
# )
# soup3 = BeautifulSoup(response3.data, 'html.parser')
# table_html3 = soup3.find_all('table')
# data_frame3 = pd.read_html(StringIO(str(table_html3)))[0]
# for i in range(len(data_frame3)):
#     if data_frame3.iloc[i, 1] == "期貨合計":
#         small_oi = int(data_frame3.iloc[i, 13])
#         print(small_oi)
#
# response4 = http3.request(
#   'POST',
#   url3,
#   fields={
#     'queryType': 1,
#     'doQuery': 1,
#     'commodityId': "TMF",
#     'queryDate': query_date
#   }
# )
# soup4 = BeautifulSoup(response4.data, 'html.parser')
# table_html4 = soup4.find_all('table')
# data_frame4 = pd.read_html(StringIO(str(table_html4)))[0]
# for i in range(len(data_frame4)):
#     if data_frame4.iloc[i, 1] == "期貨合計":
#         mini_oi = int(data_frame4.iloc[i, 13])
#         print(mini_oi)
#
# print("小台散戶多空比")
# print(round(-100*small_oi/small_total_oi, 2), "%")
# print("微台散戶多空比")
# print(round(-100*mini_oi/mini_total_oi, 2), "%")

##
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

# 主程式
query_date = "2025/06/06"

# 抓資料
small_total_oi = fetch_total_oi_from_daily_report(query_date, "MTX")
mini_total_oi = fetch_total_oi_from_daily_report(query_date, "TMF")
small_legal_oi = fetch_legal_total_oi(query_date, "MXF")
mini_legal_oi = fetch_legal_total_oi(query_date, "TMF")

# 計算與輸出
if small_total_oi and small_legal_oi:
    small_ratio = round(-100 * small_legal_oi / small_total_oi, 2)
    print(f"小台散戶多空比: {small_ratio} %")
else:
    print("小台資料不足，無法計算")

if mini_total_oi and mini_legal_oi:
    mini_ratio = round(-100 * mini_legal_oi / mini_total_oi, 2)
    print(f"微台散戶多空比: {mini_ratio} %")
else:
    print("微台資料不足，無法計算")
