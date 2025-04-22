import sqlite3

conn = sqlite3.connect('telegram_bot.db')

cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT
)
''')

conn.commit()
cursor.close()
conn.close()