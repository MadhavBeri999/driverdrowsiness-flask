# state.py
import sqlite3
import os
import uuid
from datetime import datetime

# ------------------------------
# Global in-memory alert counts
# ------------------------------
alert_counts = {"yawn": 0, "sleep": 0, "head_tilt": 0}

# ------------------------------
# Threshold for triggering alerts
# ------------------------------
ALERT_THRESHOLD = 5

# ------------------------------
# Database path
# ------------------------------
DB_PATH = os.path.join(os.getcwd(), "database", "driver_drowsiness.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_active_session(user_id: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE user_id = ? AND is_active = 1", (user_id,))
    row = c.fetchone()

    if row:
        session_id = row["id"]
    else:
        session_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO sessions (id, user_id, start_time, is_active) VALUES (?, ?, ?, 1)",
            (session_id, user_id, datetime.now()),
        )
        conn.commit()

    conn.close()
    return session_id


def get_driver_name(user_id: str) -> str:
    """
    Fetch driver_name from database by user_id.
    Returns 'Unknown Driver' if not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return "Unknown Driver"


def log_alert(user_id: str, alert_type: str):
    if alert_type not in alert_counts:
        print(f"[state.py] ⚠️ Unknown alert type: {alert_type}")
        return False

    alert_counts[alert_type] += 1
    print(f"[state.py] 🔄 {alert_type} count updated to {alert_counts[alert_type]}")

    session_id = get_active_session(user_id)
    conn = get_db_connection()
    c = conn.cursor()

    try:
        alert_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO alerts (id, session_id, alert_type, timestamp, count) VALUES (?, ?, ?, ?, ?)",
            (
                alert_id,
                session_id,
                alert_type,
                datetime.now(),
                alert_counts[alert_type],
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"[state.py] ❌ Error logging alert: {e}")
    finally:
        conn.close()

    if alert_counts[alert_type] >= ALERT_THRESHOLD:
        print(
            f"[state.py] 🚨 {alert_type.upper()} threshold exceeded! Trigger notification."
        )
        alert_counts[alert_type] = 0
        return True
    return False


def reset_alert_counts():
    for key in alert_counts:
        alert_counts[key] = 0
    print("[state.py] ✅ Alert counts reset.")
