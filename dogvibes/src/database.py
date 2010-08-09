import sqlite3

class Database():
    def __init__(self):
        self.statements = []
        self.connection = sqlite3.connect('dogvibes.db')
        # Enable returning tuples instead of just an string array
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        # Table for storing results from indexing a file system
        self.add_statement('''create table if not exists collection (id INTEGER PRIMARY KEY, track_id INTEGER)''')
        # Table for users, probably similar to a twitter user?
        self.add_statement('''create table if not exists users (id INTEGER PRIMARY KEY, vote_id INTEGER, username STRING, avatar_url STRING)''')
        # Table with votes
        self.add_statement('''create table if not exists votes (id INTEGER PRIMARY KEY, user_id INTEGER, entry_id INTEGER)''')
        # Table for storing information of all tracks that has passed through
        # dogvibes in any way, like added to a queue of playlist. This way we
        # are able to keep track of properties such as play count and can
        # reference tracks by an unique dogvibes id, rather than an uri which
        # can change over time.
        self.add_statement('''create table if not exists tracks (id INTEGER PRIMARY KEY, title TEXT, artist TEXT, album TEXT, album_uri TEXT, uri TEXT, duration INTEGER, track_number INTEGER, disc_number INTEGER, popularity FLOAT)''')
        # Table for storing playlists
        self.add_statement('''create table if not exists playlists (id INTEGER PRIMARY KEY, name TEXT)''')
        # Table for storing the relation between playlists and tracks, i.e.
        # the contents of a playlists as references
        self.add_statement('''create table if not exists entry (id INTEGER PRIMARY KEY, playlist_id INTEGER, track_id INTEGER, position INTEGER)''')
        self.commit()

    def commit_statement(self, statement, args = []):
        self.cursor.execute(statement, args)
        self.connection.commit()

    def add_statement(self, statement, args = []):
        self.statements.append((statement, args))

    def commit(self):
        map(lambda x: self.cursor.execute(x[0], x[1]), self.statements)
        self.connection.commit()
        self.statements = []

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(zip(row.keys(), row)) if row != None else None

    def fetchall(self):
        return self.cursor.fetchall()

    # TODO: check that this is always the same as the 'id' field after an insert
    def inserted_id(self):
        return self.cursor.lastrowid

if __name__ == '__main__':
    os.remove("dogvibes.db")
    db = Database()
    db.commit_statement('''insert into playlists (name) values (?)''', ["qurkloxuiikkolkjhhf0"])
