import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from datetime import date, timedelta
import os
from io import StringIO

def fetch_taifex_data():
    url = 'https://www.taifex.com.tw/cht/3/futContractsDate'
    response = requests.get(url)
    response.encoding = 'utf-8'  # 設定編碼為 UTF-8
    return response.text  # 使用 .text 來取得解碼後的內容

def parse_data(content):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(content, 'html.parser')
    numbers = soup.find_all('span', class_='blue')
    for num in numbers:
        print(num.text)
    # 美化並印出 HTML
    # print(soup.prettify())  # 使用 prettify() 方法來美化並輸出
    return None

def send_line_message(text):
    CHANNEL_ACCESS_TOKEN = '你的 channel access token'
    USER_ID = '使用者的 LINE ID（不是名字！）'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'to': USER_ID,
        'messages': [{
            'type': 'text',
            'text': text
        }]
    }

    res = requests.post('https://api.line.me/v2/bot/message/push', json=data, headers=headers)
    print(res.status_code, res.text)

def get_taiex_futures_info(): # 台指期三大法人交易資訊
    today = (date.today() - timedelta(days=1)).strftime('%Y/%m/%d')
    http = urllib3.PoolManager()
    url = "https://www.taifex.com.tw/cht/3/futContractsDate"
    res = http.request(
        'POST',
        url,
        fields={
            'queryType': 1,
            'doQuery': 1,
            'queryDate': today # today
        }
    )
    html_doc = res.data
    soup = BeautifulSoup(html_doc, 'html.parser')
    table = soup.find_all('table')
    df = pd.read_html(StringIO(str(table)))[0]
    total = df.iloc[71, 13] # 外資期貨不限商品，總未平倉口數
    TXI = df.iloc[2, 13] # 外資期貨台股期貨，總未平倉口數
    return today, TXI, total

if __name__ == '__main__':

    total, TXI, today = get_taiex_futures_info()
    print(f'{today}\n今天外資大台未平倉口數為 {TXI:,} 口\n外資期貨總計未平倉口數為 {total:,} 口\n')
    # content = fetch_taifex_data()
    # print(content)
    # message = parse_data(content)
    # print(message)
    # send_line_notify(message)
