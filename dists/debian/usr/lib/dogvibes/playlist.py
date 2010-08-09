from database import Database
from track import Track

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Playlist():
    def __init__(self, id, name, db):
        self.id = str(id)
        self.name = name
        self.db = db

    def to_dict(self):
        return dict(name = self.name, id = self.id)

    @classmethod
    def get(self, id):
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(id)])
        row = db.fetchone()
        if row == None:
            raise DogError, 'Could not get playlist with id=' + id
        return Playlist(id, row['name'], db)

    @classmethod
    def get_by_name(self, name):
        db = Database()
        db.commit_statement('''select * from playlists where name = ?''', [name])
        row = db.fetchone()
        if row == None:
            raise DogError, 'Could not get playlist with id=' + id
        return Playlist(row['id'], row['name'], db)

    @classmethod
    def name_exists(self, name):
        db = Database()
        db.commit_statement('''select * from playlists where name = ?''', [name])
        row = db.fetchone()
        if row == None:
            return False
        else:
            return True

    @classmethod
    def get_all(self):
        db = Database()
        db.commit_statement('''select * from playlists''')
        row = db.fetchone()
        playlists = []
        while row != None:
            playlists.append(Playlist(row['id'], row['name'], db))
            row = db.fetchone()
        return playlists

    @classmethod
    def create(self, name):
        db = Database()
        db.commit_statement('''insert into playlists (name) values (?)''', [name])
        print "Adding playlist '" + name + "'"
        return Playlist(db.inserted_id(), name, db)

    @classmethod
    def remove(self, id):
        db = Database()
        db.add_statement('''delete from playlist_tracks where playlist_id = ?''', [int(id)])
        db.add_statement('''delete from playlists where id = ?''', [int(id)])
        db.commit()

    # returns: the id so client don't have to look it up right after add
    def add_track(self, track):
        track_id = track.store()
        self.db.commit_statement('''insert into playlist_tracks (playlist_id, track_id) values (?, ?)''', [int(self.id), int(track_id)])
        return self.db.inserted_id()

    def remove_track(self, id):
        # There'll be no notification if the track doesn't exists
        self.db.commit_statement('''delete from playlist_tracks where id = ?''', [int(id)])

    # returns: an array of Track objects
    def get_all_tracks(self):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ?''', [int(self.id)])
        row = self.db.fetchone()
        tracks = []
        while row != None:
            tracks.append((str(row['id']), row['track_id'])) # FIXME: broken!
            row = self.db.fetchone()

        ret_tracks = []
        for track in tracks:
            # TODO: replace with an SQL statement that instantly creates a Track object
            self.db.commit_statement('''select * from tracks where id = ?''', [track[1]])
            row = self.db.fetchone()
            del row['id']
            t = Track(**row)
            t.id = track[0] # add the playlist-to-track id instead
            ret_tracks.append(t)

        return ret_tracks

    def get_track_nbr(self, nbr):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ?''', [int(self.id)])

        row = self.db.fetchone()

        # There is probably a much smarter way to fetch a specific row number
        i = 0
        while i < nbr:
            row = self.db.fetchone()
            i = i + 1

        tid = row['id']

        self.db.commit_statement('''select * from tracks where id = ?''', [row['track_id']])
        row = self.db.fetchone()
        del row['id']
        t = Track(**row)
        t.id = tid
        return t

    def remove_track_nbr(self, nbr):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ?''', [int(self.id)])

        row = self.db.fetchone()

        # There is probably a much smarter way to fetch a specific row number
        i = 0
        while i < nbr:
            row = self.db.fetchone()
            i = i + 1

        # There'll be no notification if the track doesn't exists
        self.db.commit_statement('''delete from playlist_tracks where id = ?''', [row['id']])

    def length(self):
        # FIXME this is insane we need to do a real sql count here
        i = 0
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ?''', [int(self.id)])

        row = self.db.fetchone()

        while row != None:
            i = i + 1
            row = self.db.fetchone()

        return i

if __name__ == '__main__':

    p = Playlist.create("testlist 1")
    p = Playlist.create("testlist 2")
    p = Playlist.create("testlist 3")
    print p.name
    t = Track("dummy-uri0")
    p.add_track(t)
    print p.get_all_tracks()
    try:
        p = Playlist.get('1000') # should not crash
    except DogError: pass
    p = Playlist.get('2')
    print p.name
    ps = Playlist.get_all()
    print ps[1].name
    t = Track("dummy-uri1")
    ps[0].add_track(t)
    t = Track("dummy-uri2")
    ps[0].add_track(t)
    t = Track("dummy-uri3")
    ps[0].add_track(t)
    print ps[0].get_all_tracks()
    ps[0].remove_track('2')
    print ps[0].get_all_tracks()
    print [playlist.to_dict() for playlist in Playlist.get_all()]
