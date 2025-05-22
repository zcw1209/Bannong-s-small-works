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

import time

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
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    url = "https://www.cpbl.com.tw/standings/season"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "el-table__body"))
        )
    except:
        print("等待表格載入時失敗")
        driver.quit()
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    table = soup.find("table", class_="el-table__body")
    if table is None:
        print("無法找到表格，網站結構可能已更新")
        return

    team_data = []
    for row in table.find_all("tr"):
        columns = row.find_all("td")
        if len(columns) >= 8:
            team_data.append([col.text.strip() for col in columns[:8]])

    # **建立 SQLite 資料庫（如果不存在）**
    conn = sqlite3.connect("cpbl_records.db")
    c = conn.cursor()

    # **建立資料表**
    c.execute("""
        CREATE TABLE IF NOT EXISTS cpbl_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT UNIQUE,
            games INTEGER,
            wins INTEGER,
            losses INTEGER,
            draws INTEGER,
            win_percentage REAL,
            gb TEXT,
            streak TEXT
        )
    """)

    # **清除舊資料**
    c.execute("DELETE FROM cpbl_records")

    # **插入或更新資料**
    for team in team_data:
        c.execute('''
            INSERT INTO cpbl_records (team, games, wins, losses, draws, win_percentage, gb, streak)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(team) DO UPDATE SET
                games = excluded.games,
                wins = excluded.wins,
                losses = excluded.losses,
                draws = excluded.draws,
                win_percentage = excluded.win_percentage,
                gb = excluded.gb,
                streak = excluded.streak
        ''', (
            team[0], int(team[1]), int(team[2]), int(team[3]),
            int(team[4]), float(team[5]), team[6], team[7]
        ))

    # **確認資料表是否已成功更新**
    c.execute("SELECT COUNT(*) FROM cpbl_records")
    count = c.fetchone()[0]
    print(f"資料表目前共有 {count} 筆資料")

    conn.commit()
    conn.close()

    # **更新最後更新時間**
    with open("last_update_time.txt", "w") as f:
        f.write(datetime.now().isoformat())

    print("球隊戰績已成功更新並存入 SQLite 資料庫！")




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
        "description": "Frankie 阿奇登場於富邦悍將自2017年更名後，如同威風凜凜的隊伍名稱，頭上戴著一頂具有騎士風格的頭盔，象徵他作為球隊守護者，展現堅毅不屈的形象，是富邦悍將的人氣明星。雖然外表高冷，但臉上總是掛著一抹自信的微笑、不失親民，是陪伴球隊與球迷走過高光和低谷時刻的重要夥伴！"
    },
    "Bonnie": {
        "team": "富邦悍將",
        "description": "甜美的臉蛋加上俏皮討人喜愛的個性，Bonnie總是能將周圍的人迷得神魂顛倒，是一位善於關心他人且富有正義感的小仙子。"
    },
    "猿氣小子": {
        "team": "樂天桃猿",
        "description": "樂天桃猿的吉祥物有猿氣小子Monkey、大聖Victor、Rocky，其中擁有大眼睛的猿氣小子誕生於前身Lamigo桃猿時代，當時頭身都還為亮麗水藍色。猿氣小子象徵靈活、聰明，外表陽光且個性俏皮，KPOP舞蹈、賣萌都難不倒，還非常愛搞怪，是搞笑擔當來著。有趣的是，先前因「抱粒猿事件」而讓猿氣小子被網友戲稱為「色猴」，美女在哪，他就在哪！"
    },
    "大聖": {
        "team": "樂天桃猿",
        "description": "中職_樂天桃猿的最強壯吉祥物"
    },
    "Rocky": {
        "team": "樂天桃猿",
        "description": "中職_樂天桃猿的最大隻吉祥物"
    },
    "威弟": {
        "team": "味全龍",
        "description": "味全龍的吉祥物是三兄妹，包括威弟、猛哥和芮美。其中穿著經典紅白配色球衣、戴著頭盔，還長著可愛龍角的威弟，來自「龍之子」的概念，象徵著味全重返中職後的新生力量與未來希望。他不僅為憨萌又可愛的親善大使，也經常在氣氛緊張時扮鬼臉、裝萌，讓觀眾會心一笑。此外，威弟還經常跟隨味全龍參與不少公益活動，傳遞正能量！"
    },
    "猛哥":{
        "team": "味全龍",
        "description": "三兄妹的領袖大哥－猛哥，是龍軍骨幹「狂龍軍」團長 ，個性剛毅、具強烈正義感，對勝利更是充滿渴望👊！ 總在戰場最前線鼓舞團隊，並無時無刻以健身、棒球鍛 鍊自我🥋，誓要以最強的氣勢帶領龍眾迎戰對手。"
    },
    "芮美":{
        "team": "味全龍",
        "description": "自小熱愛跳舞與表演💃，遠赴韓國學習才藝，如今因猛哥親自邀請而回歸，並接下應援團「龍粉特務教官」的重任！ 機智伶俐、充滿熱情活力的芮美，將為龍隊主場增添更多可愛魅力✨"
    },
    "萊恩":{
        "team":"統一獅",
        "description":"「國際名獅」萊恩擁有一頭狂野的橘髮，設計線條相當俐落，既保有野性又不失可愛，是融合了「王者氣息」和「萌感」的最佳代表。萊恩首次登場時以帥氣投手之姿現身，氣勢超強，個性活潑好動，還喜歡做些搞怪的舉動逗大家笑，或許外表看不出來，但其實還是地板舞蹈動作的強者！"
    },
    "盈盈":{
        "team":"統一獅",
        "description":"萊恩的啦啦隊女朋友盈盈，萊恩棒球場上介紹她是個淘氣、調皮、活潑的女生，是個會活耀氣氛的開心果。"
    },
    "小翔":{
        "team": "中信兄弟",
        "description": "小翔是進化成能用兩隻腳走路的大象，還自稱「國民男友」、「師奶殺手」，在球場上則是大家的開心果，和觀眾擊掌、抱抱、自拍樣樣來，還會亂入啦啦隊成員的舞台（笑），親和力極佳，深受大小朋友喜愛。小翔連結了兄弟象的過往輝煌歷史與新世代傳承，勝利時的歡呼、落敗後的默默陪伴，他總是和球迷們一起又哭又笑，共同見證兄弟象的成長！"
    },
    "艾比":{
        "team":"中信兄弟",
        "description":"小翔的姊姊，也是中信兄弟的吉祥物，在小翔在球場搗蛋時，會去管教弟弟，但有時候也會跟著小翔一起在球場玩耍，喜歡跟小朋友一起玩、在球場跳應援，為中信兄弟加油，大家在球場看到艾比，記得要跟她打招呼喔！"
    },
    "Tako":{
        "team":"台鋼雄鷹",
        "description":"台鋼雄鷹成立於2022年，是目前中華職棒裡最年輕的球隊。而他們的吉祥物TAKAO，取名靈感來自主場高雄的舊地名「打狗」，球衣背號為高雄區碼「07」，又和老鷹的日語「たか」發音相近，不僅展現對高雄的熱愛，更完美融合了在地歷史與隊名精神。TAKAO是一隻象徵速度和力量的帥氣老鷹，基於台灣鋼鐵集團產業背景的前瞻性，希望球隊劃破天際、展翅高飛！"
    },
    "Takamei":{
        "team":"台鋼雄鷹",
        "description":"希望球迷朋友能夠喜歡TAKAMEI，就像喜歡TAKAO一樣，愛屋及烏的心情來迎接台鋼雄鷹新的吉祥物。"
    }
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

    # 預設資料夾與檔名格式
    static_folder = "static/mascots/"
    image_path = None
    video_path = None

    # 嘗試找圖片（支援多種副檔名）
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        file_path = os.path.join(static_folder, mascot_name + ext)
        if os.path.exists(file_path):
            image_path = f"mascots/{mascot_name}{ext}"
            break

    # 嘗試找影片（如果有的話）
    for ext in ['.mp4', '.webm']:
        file_path = os.path.join(static_folder, mascot_name + ext)
        if os.path.exists(file_path):
            video_path = f"mascots/{mascot_name}{ext}"
            break

    return render_template("mascot_info.html",
                           team=mascot["team"],
                           mascot_name=mascot_name,
                           description=mascot["description"],
                           image_path=image_path,
                           video_path=video_path)


                                                                                     

if __name__ == "__main__":
    app.run(debug=True)
