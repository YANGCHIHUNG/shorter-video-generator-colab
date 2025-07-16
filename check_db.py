import sqlite3

conn = sqlite3.connect('instance/users.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', cursor.fetchall())

cursor.execute('SELECT COUNT(*) FROM user')
print('User count:', cursor.fetchone()[0])

conn.close()
