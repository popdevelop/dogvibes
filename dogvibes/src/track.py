from database import Database

class Track:
    # Set all attributes as parateters to be able to initialize with a **dict
    def __init__(self, uri, title = 'Name', artist = 'Artist', album = 'Album',
                 duration = 0, album_uri = '', votes = -1):
        self.title = title
        self.artist = artist
        self.album = album
        self.album_uri = album_uri
        self.uri = uri
        self.duration = duration
        self.id = -1
        self.votes = votes
        self.voters = []
    def __str__(self):
        return self.artist + ' - ' + self.title

    @classmethod
    def find(self, id):
        db = Database()
        db.commit_statement('''select * from playlist_tracks where id = ?''', [int(id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get track with id=' + str(id))
        track_id = row['track_id']
        votes = row['votes']

        # TODO: this could be a part of the previous statement
        db.commit_statement('''select * from tracks where id = ?''', [track_id])
        row = db.fetchone()

        return Track(row['uri'], row['title'], row['artist'], row['album'],
                     row['duration'], row['album_uri'], votes)


    # Store track for the future
    def store(self):
        db = Database()
        # TODO: don't search on uri, do a comparison on more metadata
        db.commit_statement('''select * from tracks where uri = ?''', [self.uri])
        row = db.fetchone()
        if row == None:
            db.commit_statement('''insert into tracks (title, artist, album, album_uri, uri, duration) values (?, ?, ?, ?, ?, ?)''',
                                (self.title, self.artist, self.album, self.album_uri, self.uri, self.duration))
            self.id = db.inserted_id()
        else:
            self.id = row['id']
        return self.id

    def has_vote_from(self, user_id):
        db = Database()

        db.commit_statement('''select * from votes where track_id = ? AND user_id = ?''', [self.id, user_id])
        row = db.fetchone()
        return row != None

    def get_all_voting_users(self, track_id):
        db = Database()

        ret = []

        db.commit_statement('''select * from votes join users on votes.user_id = users.id where track_id = ?''', [track_id])
        
        row = db.fetchone()
        while row != None:
            ret.append({"username":row['username'], "avatar_url":row['avatar_url']})
            row = db.fetchone()

        return ret

if __name__ == '__main__':
    print Track.find(13)
