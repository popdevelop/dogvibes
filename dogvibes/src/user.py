from database import Database
import logging
import time


class User:
    all_votes = []

    def __init__(self, username, avatar_url="http://dogvibes.com"):
        if username == None:
            self.username = "dogvibes"
        else:
            self.username = username
        self.avatar_url = avatar_url
        self.votes = 5
        self.id = -1
    def __str__(self):
        return "username: " + self.username + " id:" + str(self.id) + " avatar: " + self.avatar_url + " votes: " + str(self.votes)

    # TODO: maybe possible to make this method so that it is called automatically in
    # certain situations
    def serialize(self):
        return { "id": self.id,
                 "username": self.username,
                 "avatar_url": self.avatar_url,
                 "votes": self.votes,
                 "voted_tracks": self.get_voted_tracks()
                 }

    @classmethod
    def find_by_username(self, username):
        db = Database()
        db.commit_statement('''select * from users where username = ?''', [username])
        u = db.fetchone()
        if u == None:
            return None
        user = User(username, u['avatar_url'])
        user.id = u['id']
        user.votes = u['votes']
        return user

    @classmethod
    def find_by_or_create_from_username(self, username, avatar_url):
        user = User.find_by_username(username)
        if user == None:
            user = User(username, avatar_url)
            user.store()
        return user

    def get_voted_tracks(self):
        db = Database()

        db.commit_statement('''select votes.track_id from votes join users on votes.user_id = users.id where users.id = ?''', [str(self.id)])
        row = db.fetchone()
        track_ids = []
        while row != None:
            track_ids.append(row['track_id'])
            row = db.fetchone()

        tracks = []
        for track_id in track_ids:
            db.commit_statement('''select * from tracks where tracks.id = ?''', [track_id])
            row = db.fetchone()
            del row['id']
            tracks.append(row)

        return tracks

    # Store user, if not already added
    def store(self):
        db = Database()
        db.commit_statement('''select * from users where username = ?''', [self.username])
        u = db.fetchone()
        if  u == None:
            db.commit_statement('''insert into users (username, avatar_url, votes) VALUES(?, ?, ?)''', [self.username, self.avatar_url, self.votes])
            db.commit_statement('''select * from users where username = ?''', [self.username])
            u = db.fetchone()
            logging.debug("Added user=%s" % self.username)

        self.id = u['id']
        return u['id']
    def votes_left(self):
        db = Database()
        db.commit_statement('''select * from users where username = ?''', [self.username])
        u = db.fetchone()
        return u['votes']

    def voteup(self, track_id):
        if self.votes_left() < 1:
            logging.warning("No votes left for %s" % self.username)
            return

        db = Database()
        db.commit_statement('''select * from tracks where id=?''', [track_id])
        row = db.fetchone()

        now = time.time()

        self.all_votes.append({"id":track_id,"title":row['title'], "artist":row['artist'], "album": row['album'], "user":self.username, "avatar_url": self.avatar_url, "time":now, "votes":1, "duration":row['duration'], "votes":3, "uri": row["uri"]})

        db.commit_statement('''insert into votes (track_id, user_id) values (?, ?)''', [track_id, self.id])
        # take vote from user
        db.commit_statement('''update users set votes = votes - 1 where id = ?''', [self.id])
        logging.debug("Update number of votes and track votes for user = %s" % self.username)

    def votedown(self, track_id):
        db = Database()
        db.commit_statement('''delete from votes where track_id = ? and user_id = ?''', [track_id, self.id])
        # give vote back to user
        db.commit_statement('''update users set votes = votes + 1 where id = ?''', [self.id])
        logging.debug("Update number of votes and track votes for user = %s" % self.username)

    @classmethod
    def remove_all_voting_users(self, track_id):
        db = Database()
        db.commit_statement('''select * from votes where track_id = ?''', [track_id])
        
        logging.debug("Give votes back to all users who voted for removed track %s" % track_id)

        user_ids = []
        row = db.fetchone()
        while row != None:
            user_ids.append(row['user_id'])
            row = db.fetchone()
        
        for id in user_ids:
            logging.debug("%s voted for track %s now got one vote back" % (id, track_id))
            # give vote back to user
            db.commit_statement('''update users set votes = votes + 1 where id = ?''', [id])
            row = db.fetchone()

        db.commit_statement('''delete from votes where track_id = ?''', [track_id])
            
    @classmethod
    def get_activity(self, limit):
        tmp = self.all_votes[:]
        tmp.reverse()
        return tmp[:limit]

if __name__ == '__main__':
    user = User.find_by_username("brissmyr")
