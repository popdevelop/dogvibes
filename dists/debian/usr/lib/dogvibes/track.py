from database import Database

class Track:
    # Set all attributes as parateters to be able to initialize with a **dict
    def __init__(self, uri, title = 'Name', artist = 'Artist', album = 'Album',
                 duration = 0):
        self.title = title
        self.artist = artist
        self.album = album
        self.uri = uri
        self.duration = duration

    def __str__(self):
        return self.artist + ' - ' + self.title

    # Store track for the future
    def store(self):
        db = Database()
        # TODO: don't search on uri, do a comparison on more metadata
        db.commit_statement('''select * from tracks where uri = ?''', [self.uri])
        row = db.fetchone()
        if row == None:
            db.commit_statement('''insert into tracks (title, artist, album, uri, duration) values (?, ?, ?, ?, ?)''',
                                (self.title, self.artist, self.album, self.uri, self.duration))
            return db.inserted_id()
        else:
            return row['id']
