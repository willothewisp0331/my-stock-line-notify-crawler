import requests
import pandas as pd
from bs4 import BeautifulSoup
import os

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

if __name__ == '__main__':
    content = fetch_taifex_data()
    # print(content)
    message = parse_data(content)
    # print(message)
    # send_line_notify(message)
