import sqlite3
from Core.db import create_tables

create_tables()

conn = sqlite3.connect("cdss.db")
for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(name)
conn.close()