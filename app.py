from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    conn = sqlite3.connect("cpbl_records.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT team, games, wins, losses, draws, win_rate FROM cpbl_teams")
    teams = cursor.fetchall()
    
    conn.close()
    
    return render_template("index.html", teams=teams)

if __name__ == "__main__":
    app.run(debug=True)