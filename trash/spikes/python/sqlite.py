import sys
import os
import sqlite3  # requires deb python-sqlite

db = 'dogvibes.db'

if os.path.exists(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
else:
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''create table collection (id INTEGER PRIMARY KEY, name TEXT, artist TEXT, album TEXT, uri TEXT, duration INTEGER)''')

# Insert track
c.execute("insert into collection (name, artist, album, uri, duration) values (?, ?, ?, ?, ?)", ('Marathon', 'Head Unit', '72k Color Sound', 'file:///head.mp3', 142000))

# Save (commit) the changes
conn.commit()

query = '%Marathon%'
c.execute("select * from collection where name LIKE ? or artist LIKE ? or album LIKE ? or uri LIKE ?", (query, query, query, query))
for row in c:
    print row[2] + " - " + row[1]

# We can close the cursor if we are done with it
c.close()
