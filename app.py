from flask import Flask, render_template, redirect, url_for
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
#限制更新頻率
import os
from datetime import datetime, timedelta

app = Flask(__name__)

LAST_UPDATE_FILE = "last_update_time.txt"
UPDATE_INTERVAL = timedelta(minutes=10)

def is_update_allowed():
    if not os.path.exists(LAST_UPDATE_FILE):
        return True
    with open(LAST_UPDATE_FILE, "r") as f:
        last_time_str = f.read().strip()
    try:
        last_time = datetime.fromisoformat(last_time_str)
    except:
        return True
    return datetime.now() - last_time > UPDATE_INTERVAL

def update_last_update_time():
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(datetime.now().isoformat())

def fetch_cpbl_data():
    chromedriver_autoinstaller.install()
    URL = "https://www.cpbl.com.tw/standings/season"
    driver = webdriver.Chrome()
    driver.get(URL)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "RecordTableWrap"))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    record_table = soup.find("div", class_="RecordTableWrap")
    if record_table is None:
        return

    teams = []
    table_rows = record_table.find_all("tr")[1:]
    for row in table_rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        team_name = cols[0].text.strip()
        games = int(cols[1].text.strip())
        try:
            win_str = cols[2].text.strip()
            wins, draws, losses = map(int, win_str.split("-"))
        except:
            continue
        try:
            win_rate = float(cols[3].text.strip())
        except:
            win_rate = 0.0

        teams.append({
            "team": team_name,
            "games": games,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": win_rate
        })

    conn = sqlite3.connect("cpbl_records.db")
    cursor = conn.cursor()
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

# 吉祥物資料（假設手動先寫好）
mascots = [
{"team": "味全龍", "mascots": ["威弟", "猛哥", "芮美"], "link": "/mascot/dragons"},
{"team": "中信兄弟", "mascots": ["小翔", "艾比"], "link": "/mascot/brothers"},
{"team": "統一獅", "mascots": ["萊恩", "盈盈"], "link": "/mascot/lions"},
{"team": "富邦悍將", "mascots": ["Frankie", "Bonnie"], "link": "/mascot/guardians"},
{"team": "樂天桃猿", "mascots": ["猿氣小子", "大聖", "Rocky"], "link": "/mascot/monkeys"},
{"team": "台鋼雄鷹", "mascots": ["Tako", "Takamei"], "link": "/mascot/eagles"}
]

# 吉祥物詳細介紹資料（可以依需要繼續增加）
mascot_details = {
    "Frankie": {
        "team": "富邦悍將",
        "description": "Frankie 是富邦悍將的主吉祥物，充滿活力與戰鬥精神。"
    },
    "Bonnie": {
        "team": "富邦悍將",
        "description": "Bonnie 是富邦悍將的啦啦隊吉祥物，個性甜美。"
    },
    "猿氣小子": {
        "team": "樂天桃猿",
        "description": "猿氣小子是樂天桃猿的靈魂代表，總是充滿熱情與歡笑。"
    },
    "大聖": {
        "team": "樂天桃猿",
        "description": "大聖是樂天桃猿的戰神代表，英勇無畏。"
    },
    "Rocky": {
        "team": "樂天桃猿",
        "description": "Rocky 是樂天的搖滾猴，充滿節奏感和舞台魅力。"
    },
    "威弟": {
        "team": "味全龍",
        "description": "威弟是味全龍的年輕戰士，總是精神奕奕。"
    },
    # 你可以繼續補上其他吉祥物...
}


@app.route("/")
def index():
    conn = sqlite3.connect("cpbl_records.db")
    cursor = conn.cursor()
    cursor.execute("SELECT team, games, wins, losses, draws, win_rate FROM cpbl_teams")
    teams = cursor.fetchall()
    conn.close()

    return render_template("index.html", teams=teams,mascots=mascots)

@app.route("/update")
def update():
    if not is_update_allowed():
        return "更新太頻繁，請稍後再試。", 429
    fetch_cpbl_data()
    update_last_update_time()
    return redirect(url_for("index"))


# 建立網址簡寫對應
mascot_map = {m["link"].split("/")[-1]: m for m in mascots}

@app.route("/mascot/<team>")
def mascot_detail(team):
    if team in mascot_map:
        mascot = mascot_map[team]
        return render_template("mascot_detail.html", mascot=mascot)
    return "找不到這支球隊", 404


@app.route("/mascot/<team>/<mascot_name>")
def mascot_info(team, mascot_name):
    mascot = mascot_details.get(mascot_name)
    if not mascot:
        return "找不到吉祥物", 404
    return render_template("mascot_info.html", team=mascot["team"], mascot_name=mascot_name, description=mascot["description"])

                                                                                     

if __name__ == "__main__":
    app.run(debug=True)
