# inspect_db.py
import sqlite3
DB = "database/driver_drowsiness.db"

conn = sqlite3.connect(DB)
c = conn.cursor()

print("USERS:")
for row in c.execute("SELECT id, full_name, email, phone FROM users"):
    print(row)

print("\nCONTACTS:")
for row in c.execute("SELECT id, user_id, name, email, phone FROM contacts"):
    print(row)

conn.close()
