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

conn.commit()
conn.close()

print("✅ Database and tables created successfully!")
