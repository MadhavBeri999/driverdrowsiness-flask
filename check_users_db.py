import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Show table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Show schema of users table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")
schema = cursor.fetchone()
print("\nUsers table schema:\n", schema[0] if schema else "No 'users' table found.")

conn.close()
