import sqlite3
import os

# Ensure database folder exists
if not os.path.exists('database'):
    os.makedirs('database')

DB_PATH = os.path.join('database', 'driver_drowsiness.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# -------- Users Table --------
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL
)
''')

# -------- Emergency Contacts Table --------
c.execute('''
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    relation TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# -------- Sessions Table --------
# Each detection run (driving session) will create one entry here.
c.execute('''
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# -------- Alerts Table --------
# Stores every alert detected during a session.
c.execute('''
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- e.g., yawn, sleep, head_tilt
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    count INTEGER DEFAULT 1,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
)
''')

# -------- Notifications Sent Table --------
# Logs when we send alerts to emergency contacts.
c.execute('''
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
''')

conn.commit()
conn.close()

print("✅ Database and all tables created/verified successfully!")
