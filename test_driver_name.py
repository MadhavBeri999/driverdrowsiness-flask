import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "database", "driver_drowsiness.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_driver_name(user_id: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return "Unknown Driver"


if __name__ == "__main__":
    user_id = "01b4ef45-646f-4d0f-be1d-36d312483d80"  # Replace with actual ID
    print(f"Driver Name: {get_driver_name(user_id)}")
