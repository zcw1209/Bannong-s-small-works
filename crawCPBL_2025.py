# -*- coding: utf-8 -*-
"""
Created on Thu May 15 14:18:41 2025
@author: user
"""
import requests
from bs4 import BeautifulSoup
import sqlite3

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sys

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()  # 自動安裝適合的 ChromeDriver
from selenium import webdriver

# 設定中華職棒戰績網址
URL = "https://www.cpbl.com.tw/standings/season"

# 使用 Selenium 載入完整網頁
driver = webdriver.Chrome()
driver.get(URL)

# 等待戰績表格載入
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "RecordTableWrap"))
)

# 使用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# 找到戰績表格
record_table = soup.find("div", class_="RecordTableWrap")

if record_table is None:
    print("找不到 RecordTable，請檢查網頁結構或使用 Selenium 等待載入")
    sys.exit()

# 解析表格資料
teams = []
table_rows = record_table.find_all("tr")[1:]  # 跳過表頭
for row in table_rows:
    cols = row.find_all("td")
    if len(cols) < 4:
        continue  # 避免空行

    team_name = cols[0].text.strip()
    games = int(cols[1].text.strip())

    # 將 "勝-和-敗" 字串切割成三個整數
    try:
        win_str = cols[2].text.strip()
        wins, draws, losses = map(int, win_str.split("-"))
    except Exception as e:
        print(f"解析戰績資料時出錯：{e}")
        continue

    try:
        win_rate = float(cols[3].text.strip())
    except ValueError:
        win_rate = 0.0  # 若轉換失敗則設為 0.0

    team_data = {
        "team": team_name,
        "games": games,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": win_rate
    }
    teams.append(team_data)

# 建立 SQLite 資料庫並存入數據
conn = sqlite3.connect("cpbl_records.db")
cursor = conn.cursor()

# 建立資料表，team 欄位設為 UNIQUE
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cpbl_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team TEXT UNIQUE,
        games INTEGER,
        wins INTEGER,
        losses INTEGER,
        draws INTEGER,
        win_rate REAL
    )
""")

# 插入或更新資料（ON CONFLICT）
for team in teams:
    cursor.execute("""
        INSERT INTO cpbl_teams (team, games, wins, losses, draws, win_rate)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(team) DO UPDATE SET
            games = excluded.games,
            wins = excluded.wins,
            losses = excluded.losses,
            draws = excluded.draws,
            win_rate = excluded.win_rate
    """, (team["team"], team["games"], team["wins"], team["losses"], team["draws"], team["win_rate"]))

conn.commit()
conn.close()

print("球隊戰績已成功更新並存入 SQLite 資料庫！")

