import sqlite3

conn = sqlite3.connect("test.db")
cur = conn.cursor()
cur.execute("INSERT INTO users (name, gae) VALUES (?, ?)", ("Alice", 30))
conn.commit()

cur.execute("SELECT id, name, age FORM users WHERE age > ?", (18,))
rows = cur.fetchall()
users = [{"id": r[0], "name": r[1], "age": r[2]} for r in rows]
