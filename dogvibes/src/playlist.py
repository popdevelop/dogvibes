from database import Database
from track import Track
from user import User
import logging

class Playlist():
    version = 0

    def __init__(self, id, name, db):
        self.id = int(id)
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
            raise ValueError('Could not get playlist with id=' + str(id))
        return Playlist(id, row['name'], db)

    @classmethod
    def get_by_name(self, name):
        db = Database()
        db.commit_statement('''select * from playlists where name = ?''', [name])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + str(id))
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
        logging.debug ("Adding playlist '" + name + "'")
        return Playlist(db.inserted_id(), name, db)

    @classmethod
    def remove(self, id):
        self.tick_version()
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + id)

        db.add_statement('''delete from playlist_tracks where playlist_id = ?''', [int(id)])
        db.add_statement('''delete from playlists where id = ?''', [int(id)])
        db.commit()

    @classmethod
    def rename(self, playlist_id, name):
        self.tick_version()
        db = Database()
        db.commit_statement('''select * from playlists where id = ?''', [int(playlist_id)])
        row = db.fetchone()
        if row == None:
            raise ValueError('Could not get playlist with id=' + playlist_id)

        db.add_statement('''update playlists set name = ? where id = ?''', [name, int(playlist_id)])
        db.commit()

    @classmethod
    def tick_version(self):
        self.version = self.version + 1

    @classmethod
    def get_version(self):
        return self.version

    @classmethod
    def has_track(self,playlist_id, track_id):
        #check if track is present in playlist
        db = Database()
        db.commit_statement('''select * from playlist_tracks where playlist_id = ? AND track_id = ?''', [playlist_id, track_id])
        row = db.fetchone()
        return row != None

    def remove_vote(self, track, username, avatar_url):
        self.tick_version()
        user = User(username, avatar_url)
        user_id = user.store()
        track_id = track.store()

        if not track.has_vote_from(user_id):
            logging.debug("%s has no vote for track, ignoring" % user.username)
            return

        if self.has_track(self.id, track_id):
            #DOWNVOTE TRACK
            logging.debug("Downvote track_id = %s" % track_id)
            playlist_id = self.id
            db = Database()
            db.commit_statement('''select * from playlist_tracks where playlist_id = ? AND track_id = ? LIMIT 1''', [playlist_id, track_id])
            row = db.fetchone()
            pos = row['position']
            votes = row['votes']
            votes = votes - 1

            if votes == 0:
                logging.debug("Track has no more votes remove track from playlist")
                db.commit_statement('''select * from playlist_tracks where track_id = ? and playlist_id = ?''', [track_id, self.id])
                row = db.fetchone()
                self.remove_playlist_tracks_id(row['id'])
                return

            # find all with same amount of votes, and move pass them
            db.commit_statement('''select min(position) as new_pos,* from playlist_tracks where playlist_id = ? AND votes = ? AND position > 1''', [playlist_id, votes])
            # update votes
            row = db.fetchone()
            if row == None:
                logging.debug("no need to move, no one to pass with %s votes" % votes)
            else:
                #we have some tracks to jump over
                new_pos = row['new_pos']
                if new_pos <= 1:
                    logging.debug("cap movement to pos=2 (let playing song be first)")
                    new_pos=2
                logging.debug("update pos, move from %s to %s" % (str(pos), str(new_pos)))
                #move them up 1 position
                db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position >= ?''', [self.id, new_pos])
                #put me below them
                db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and track_id = ?''', [new_pos, self.id, track_id])

            #update the votes on the track
            db.commit_statement('''update playlist_tracks set votes = votes - 1 where playlist_id = ? and track_id = ?''', [self.id, track_id])
            user.votedown(track_id)
        else:
            logging.debug("Down voting track does not exists in database")

    def add_vote(self, track, username, avatar_url):
        self.tick_version()
        user = User(username, avatar_url)
        user_id = user.store()
        track_id = track.store()

        if user.votes_left() < 1:
            logging.debug("No more votes left for %s" % user.username)
            return

        if track.has_vote_from(user_id):
            logging.debug("%s already voted for track, ignoring" % user.username)
            return

        if self.has_track(self.id, track_id):
            #UPVOTE TRACK
            logging.debug("Upvote track_id = %s" % track_id)
            playlist_id = self.id
            db = Database()
            db.commit_statement('''select * from playlist_tracks where playlist_id = ? AND track_id = ? LIMIT 1''', [playlist_id, track_id])
            row = db.fetchone()
            pos = row['position']
            votes = row['votes']

            # we dont want to move pass the playing track
            if pos <= 2:
                logging.debug("no need to move, at position = %s" % pos)
            else:
                # find all with same amount of votes, and move pass them
                db.commit_statement('''select min(position) as new_pos,* from playlist_tracks where playlist_id = ? AND votes = ? AND position > 1''', [playlist_id, votes])
                # update votes
                row = db.fetchone()
                if row == None:
                    logging.debug("no need to move, no one to pass with %s votes" % votes)
                else:
                    #we have some tracks to jump over
                    new_pos = row['new_pos']
                    if new_pos <= 1:
                        logging.debug("cap movement to pos=2 (let playing song be first)")
                        new_pos=2
                    logging.debug("update pos, move from %s to %s" % (str(pos), str(new_pos)))
                    #move them down 1 position
                    db.commit_statement('''update playlist_tracks set position = position + 1 where playlist_id = ? and position >= ?''', [self.id, new_pos])
                    #put me above them
                    db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and track_id = ?''', [new_pos, self.id, track_id])

            #update the votes on the track
            db.commit_statement('''update playlist_tracks set votes = votes + 1 where playlist_id = ? and track_id = ?''', [self.id, track_id])
        else:
            #ADD TRACK
            logging.debug("add track with track_id = %s" % track_id)
            self.add_track(track, 1)

        #update user votes
        user.voteup(track_id)

    def add_track(self, track, votes):
        self.tick_version()
        track_id = track.store()

        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()

        if row['max(position)'] == None:
            position = 1
        else:
            position = row['max(position)'] + 1

        self.db.commit_statement('''insert into playlist_tracks (playlist_id, track_id, position, votes) values (?, ?, ?, ?)''', [self.id, track_id, position, votes])
        return self.db.inserted_id()

     # returns: the id so client don't have to look it up right after add
    def add_tracks(self, tracks, position):
        first = True
        tid = 0
        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()

        if row['max(position)'] == None:
            # no tracks in queue, put it first
            position = 1
        else:
            # sanity check index
            if int(position) > int(row['max(position)']) + 1 or int(position) < 0:
                position = int(row['max(position)']) + 1
            else:
                self.db.commit_statement('''update playlist_tracks set position = position + ? where playlist_id = ? and position >= ?''', [str(len(tracks)), self.id, position])

        # add new tracks
        for track in tracks:
            track_id = track.store()

            self.db.commit_statement('''insert into playlist_tracks (playlist_id, track_id, position, votes) values (?, ?, ?,?)''', [self.id, track_id, position, 0])
            position = int(position) + 1

            if first:
                first = False
                tid = self.db.inserted_id()

        self.tick_version()
        return tid

    # returns: an array of Track objects
    def get_all_tracks(self):

        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ? order by position''', [int(self.id)])
        row = self.db.fetchone()
        tracks = []
        while row != None:
            tracks.append((str(row['id']), row['track_id'], row['votes'])) # FIXME: broken!
            row = self.db.fetchone()

        ret_tracks = []

        for track in tracks:
            # TODO: replace with an SQL statement that instantly creates a Track object
            self.db.commit_statement('''select * from tracks where id = ?''', [track[1]])
            row = self.db.fetchone()
            oldid = row['id']
            del row['id']
            t = Track(**row)
            t.id = track[0]
            t.votes = str(track[2])
            t.voters = t.get_all_voting_users(oldid)
            ret_tracks.append(t)

        return ret_tracks

    def get_track_nbr(self, nbr):
        self.db.commit_statement('''select * from playlist_tracks where playlist_id = ? order by position limit ?,1''', [int(self.id), nbr])
        return self.get_track_row()

    def get_track_id(self, id):
        self.db.commit_statement('''select * from playlist_tracks where id = ?''', [id])
        return self.get_track_row()

    def get_track_row(self):
        row = self.db.fetchone()
        tid = row['track_id']
        position = row['position']
        ptid = row['id']

        self.db.commit_statement('''select * from tracks where id = ?''', [row['track_id']])
        row = self.db.fetchone()
        del row['id']
        t = Track(**row)
        t.id = tid
        t.position = position
        t.ptid = ptid
        return t

    def move_track(self, id, position):
        self.db.commit_statement('''select position from playlist_tracks where playlist_id = ? and id = ?''', [self.id, id])
        row = self.db.fetchone()
        if row == None:
            raise ValueError('Could not find track with id=%d in playlist with id=%d' % (id, self.id))
        old_position = row['position']
        logging.debug("Move track from %s to %s" % (old_position,position))

        self.db.commit_statement('''select max(position) from playlist_tracks where playlist_id = ?''', [self.id])
        row = self.db.fetchone()

        if position > row['max(position)'] or position < 1:
            raise ValueError('Position %d is out of bounds (%d, %d)' % (position, 1, row['max(position)']))

        if position > old_position:
            self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ? and position <= ?''', [self.id, old_position, position])
            self.db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and id = ?''', [position, self.id, id])
        else:
            self.db.commit_statement('''update playlist_tracks set position = position + 1 where playlist_id = ? and position >= ?''', [self.id, position])
            self.db.commit_statement('''update playlist_tracks set position = ? where playlist_id = ? and id = ?''', [position, self.id, id])
            self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ?''', [self.id, old_position])

    def remove_playlist_tracks_id(self, id):
        self.tick_version()
        self.db.commit_statement('''select * from playlist_tracks where id = ?''', [id])

        row = self.db.fetchone()
        if row == None:
            raise ValueError('Could not find track with id=%s' % (int(id)))

        # give vote back to all users that voted
        User.remove_all_voting_users(row['track_id'])

        id = row['id']
        self.db.commit_statement('''delete from playlist_tracks where id = ?''', [row['id']])
        self.db.commit_statement('''update playlist_tracks set position = position - 1 where playlist_id = ? and position > ?''', [self.id, row['position']])

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

    from dogvibes import Dogvibes
    global dogvibes
    dogvibes = Dogvibes()
