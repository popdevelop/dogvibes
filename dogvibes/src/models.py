from django.conf import settings
settings.configure(DATABASE_ENGINE='sqlite3', DATABASE_NAME='dogvibes.db')

from django.db import models
from django.db.models import Avg, Max, Min, Count

from positional import PositionalSortMixIn

class Track(models.Model):
    title = models.CharField()
    artist = models.CharField()
    album = models.CharField()
    album_uri = models.CharField()
    uri = models.CharField()
    duration = models.IntegerField()
    disc_number = models.IntegerField()
    track_number = models.IntegerField()
    popularity = models.FloatField()

    def __unicode__(self):
        return self.title
    class Meta:
        db_table = 'tracks'
        app_label = "myapp"


class User(models.Model):
#    foo = models.ForeignKey( Foo )
    username = models.CharField()
    avatar_url = models.CharField()

    def votes_left(self):
        return 5 - User.objects.get(id=self.id).vote_set.all().count()

    def already_voted(self, track):
        return False

    def __unicode__(self):
        return self.username
    class Meta:
        db_table = 'users'
        app_label = "myapp"


class Playlist(models.Model):
    name = models.CharField()
    tracks = models.ManyToManyField(Track, through='Entry')

    version = 0

    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'playlists'
        app_label = "myapp"


class Entry(PositionalSortMixIn, models.Model):
    playlist = models.ForeignKey(Playlist)
    track = models.ForeignKey(Track)
    timestamp = models.DateField(auto_now_add=True)
    def __unicode__(self):
        return self.playlist.name + ": " + self.track.title + " ("+str(self.position)+")"
    class Meta:
        db_table = 'entry'
        app_label = "myapp"
        get_latest_by = 'timestamp'


class Vote(models.Model):
    user = models.ForeignKey(User)
    entry = models.ForeignKey(Entry)
    def __unicode__(self):
        return self.user.username + ": " + self.entry.track.title
    class Meta:
        db_table = 'votes'
        app_label = "myapp"
