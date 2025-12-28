import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "driver_drowsiness.db")


def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # -------- Users Table --------
    c.execute(
        """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL
)
"""
    )

    # -------- Emergency Contacts Table --------
    c.execute(
        """
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    relation TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
"""
    )

    # -------- Sessions Table --------
    # Each detection run (driving session) will create one entry here.
    c.execute(
        """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
"""
    )

    # -------- Alerts Table --------
    # Stores every alert detected during a session.
    c.execute(
        """
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- e.g., yawn, sleep, head_tilt
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    count INTEGER DEFAULT 1,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
)
"""
    )

    # -------- Notifications Sent Table --------
    # Logs when we send alerts to emergency contacts.
    c.execute(
        """
CREATE TABLE IF NOT EXISTS notifications_sent (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT,
    alert_type TEXT,
    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
)
"""
    )
    # -------- Companies Table --------
    c.execute(
        """
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
    )
    # -------- Company Users Table --------
    c.execute(
        """
CREATE TABLE IF NOT EXISTS company_users (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    age INTEGER,
    email TEXT,
    phone TEXT,
    vehicle_number TEXT, 
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
)
"""
    )
    # -------- Company Emergency Contacts Table --------
    c.execute(
        """
CREATE TABLE IF NOT EXISTS company_contacts (
    id TEXT PRIMARY KEY,
    company_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    relation TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    FOREIGN KEY(company_user_id) REFERENCES company_users(id) ON DELETE CASCADE
)
"""
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()


print("✅ Database and all tables created/verified successfully!")
