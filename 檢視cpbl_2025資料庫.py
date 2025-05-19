# -*- coding: utf-8 -*-
"""
Created on Thu May 15 15:22:03 2025

@author: user
"""
import sqlite3

conn = sqlite3.connect("cpbl_records.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM cpbl_teams")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
