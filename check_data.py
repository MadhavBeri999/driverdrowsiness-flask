import sqlite3

conn = sqlite3.connect('database/driver_drowsiness.db')
c = conn.cursor()

c.execute("SELECT * FROM users;")
print("Users:", c.fetchall())

c.execute("SELECT * FROM contacts;")
print("Contacts:", c.fetchall())

conn.close()
