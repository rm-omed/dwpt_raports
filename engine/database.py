import sqlite3
from datetime import datetime
import os

DB_FILE = os.path.join("data", "report_log.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS completed_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id TEXT,
            filename TEXT,
            completed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_task_completion(template_id, filename):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO completed_reports (template_id, filename, completed_at)
        VALUES (?, ?, ?)
    ''', (str(template_id), os.path.basename(filename), now))
    conn.commit()
    conn.close()

def get_completed_template_ids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT DISTINCT template_id FROM completed_reports')
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids

def get_all_completed_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT template_id, filename, completed_at FROM completed_reports ORDER BY completed_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def clear_all_completed_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM completed_reports')
    conn.commit()
    conn.close()
