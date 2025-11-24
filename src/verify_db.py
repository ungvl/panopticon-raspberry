import sqlite3
import os

db_path = "../activity_data.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM screen_events ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows:")
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error reading DB: {e}")
else:
    print("DB file not found")
