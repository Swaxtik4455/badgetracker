import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Tuple

DB_NAME = "skilltrack_history.db"

def init_db():
    """Initializes local SQLite database tables if not already created."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_profiles INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                profile_url TEXT,
                status TEXT,
                badge_count INTEGER,
                timestamp TEXT,
                FOREIGN KEY(run_id) REFERENCES verification_runs(id)
            )
        """)
        conn.commit()

def save_run(results: List[Dict[str, Any]]) -> int:
    """Saves batch verification results and returns the created run_id."""
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO verification_runs (timestamp, total_profiles) VALUES (?, ?)",
            (timestamp, len(results))
        )
        run_id = cursor.lastrowid
        
        snapshot_records = [
            (run_id, r["url"], r["status"], r["badge_count"], timestamp)
            for r in results
        ]
        cursor.executemany(
            "INSERT INTO profile_snapshots (run_id, profile_url, status, badge_count, timestamp) VALUES (?, ?, ?, ?, ?)",
            snapshot_records
        )
        conn.commit()
    return run_id

def get_previous_run_data() -> Dict[str, int]:
    """Retrieves the badge count per URL from the most recent previous run."""
    init_db()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM verification_runs")
        row = cursor.fetchone()
        if not row or row[0] is None:
            return {}
        last_run_id = row[0]

        cursor.execute(
            "SELECT profile_url, badge_count FROM profile_snapshots WHERE run_id = ?",
            (last_run_id,)
        )
        return {r[0]: r[1] for r in cursor.fetchall()}