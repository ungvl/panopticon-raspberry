import os
from dotenv import load_dotenv

load_dotenv()

import sqlite3

class DatabaseConnector:
    def __init__(self):
        self.connection_string = os.getenv("DB_CONNECTION_STRING", "sqlite:///activity_data.db")
        # Parse connection string (assuming sqlite:///path)
        if self.connection_string.startswith("sqlite:///"):
            self.db_path = self.connection_string.replace("sqlite:///", "")
        else:
            self.db_path = "../activity_data.db"
            
        print(f"[INFO] DatabaseConnector initialized with: {self.db_path}")
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS screen_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        app TEXT,
                        title TEXT,
                        duration REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS face_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        name TEXT,
                        confidence REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to initialize DB: {e}")

    def send_data(self, data):
        """
        Sends screen data to the database.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO screen_events (timestamp, app, title, duration)
                    VALUES (?, ?, ?, ?)
                """, (data['timestamp'], data['app'], data['title'], data['duration']))
                conn.commit()
            print(f"[DB] Saved screen data: {data['app']} - {data['title']}")
        except Exception as e:
            print(f"[ERROR] Failed to save screen data: {e}")

    def send_face_data(self, data):
        """
        Sends face data to the database.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO face_events (timestamp, name, confidence)
                    VALUES (?, ?, ?)
                """, (data['timestamp'], data['name'], data['confidence']))
                conn.commit()
            print(f"[DB] Saved face data: {data['name']} ({data['confidence']:.2f})")
        except Exception as e:
            print(f"[ERROR] Failed to save face data: {e}")
