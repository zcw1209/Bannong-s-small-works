from flask import Flask, render_template, redirect, url_for
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from bs4 import BeautifulSoup

app = Flask(__name__)

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

@app.route("/")
def index():
    conn = sqlite3.connect("cpbl_records.db")
    cursor = conn.cursor()
    cursor.execute("SELECT team, games, wins, losses, draws, win_rate FROM cpbl_teams")
    teams = cursor.fetchall()
    conn.close()
    return render_template("index.html", teams=teams)

@app.route("/update")
def update():
    fetch_cpbl_data()
    return redirect(url_for("index"))  # 更新完資料後重新導回首頁

if __name__ == "__main__":
    app.run(debug=True)
