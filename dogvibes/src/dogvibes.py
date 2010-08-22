import gobject
import gst
import os
import config
import sys
import shelve

import threading

from amp import Amp

# import spources
from filesource import FileSource
from spotifysource import SpotifySource
from srradiosource import SRRadioSource
#from youtubesource import YoutubeSource

from albumart import AlbumArt

# import speakers
from devicespeaker import DeviceSpeaker
from fakespeaker import FakeSpeaker

from models import Track
from models import Playlist
from models import User
from models import Entry
from database import Database

from django.forms.models import model_to_dict

class Dogvibes():
    ampdbname = "qurkloxuiikkolkjhhf"

    def __init__(self):

        # load configuration
        try: cfg = config.load("dogvibes.conf")
        except Exception, e:
            print "ERROR: Cannot load configuration file\n"
            sys.exit(1)

        # initiate
        self.needs_push_update = False
        self.search_history = []

        # create sources struct
        self.sources = shelve.open('dogvibes.shelve', writeback=True)

        # add all speakers, should also be stored in database as sources
        self.speakers = [DeviceSpeaker("devicesink"), FakeSpeaker("fakespeaker")]

        first_boot = False
        if len(self.sources) == 0:
            first_boot = True
            spot_user = cfg["SPOTIFY_USER"]
            spot_pass = cfg["SPOTIFY_PASS"]
            self.modify_spotifysource(spot_user, spot_pass)
            self.modify_srradiosource();

        # add all amps, currently only one
        amp0 = Amp(self, "0")
        amp0.connect_speaker(0)
        self.amps = [amp0]

        if first_boot == True:
            # currently connect all sources to the first amp
            for key in self.sources.keys():
                amp0.connect_source(key)

    def create_track_from_uri(self, uri):
        track = None
        for name,source in self.sources.iteritems():
            if source:
                track = source.create_track_from_uri(uri)
                if track != None:
                    return track
        raise ValueError('Could not create track from URI')

    def create_tracks_from_uri(self, uri):
        tracks = []
        for name,source in self.sources.iteritems():
            if source:
                tracks = source.create_tracks_from_uri(uri)
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from URI')

    def create_tracks_from_album(self, album):
        tracks = []
        for name,source in self.sources.iteritems():
            if source:
                tracks = source.create_tracks_from_album(album)
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from Album')

    def modify_spotifysource(self, username, password):
        if self.sources.has_key("spotify"):
            self.sources["spotify"].amp.stop()
            self.sources["spotify"].relogin(username, password)
            self.sources.sync()
        else:
            spotifysource = SpotifySource("spotify", username, password)
            self.sources["spotify"] = spotifysource
            self.sources.sync()

    def modify_srradiosource(self):
        if self.sources.has_key("srradiosource"):
            pass
        else:
            srradiosource = SRRadioSource("srradio")
            self.sources["srradio"] = srradiosource
            self.sources.sync()

    def get_all_tracks_in_playlist(self, playlist_id):
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        tracks = playlist.get_all_tracks()
        ret = [track.__dict__ for track in tracks]
        return ret

    def do_search(self, query, request):
        ret = []
#        for name,source in self.sources.iteritems():
#            if query.startswith(source.search_prefix + ":"):
#                newquery = query.split(":",1)
#                ret = source.search(newquery[1])
#                request.finish(ret)
#                return

        #if no prefix, just use spotify, if there exists such a source
        for name,source in self.sources.iteritems():
            if source.search_prefix == "spotify":
                tracks = source.search(query)
                ret = [model_to_dict(track) for track in tracks]
                request.finish(ret)
                return # TODO: shouldn't we continue here?

        request.finish(ret)

    def fetch_albumart(self, artist, album, size, request):
        try:
            request.finish(AlbumArt.get_image(artist, album, size), raw = True)
        except ValueError as e:
            request.finish(AlbumArt.get_standard_image(size), raw = True)

    def create_playlist(self, name):
        Playlist.create(name)

    def get_album(self, album_uri, request):
        album = None
        for name, source in self.sources.iteritems():
            album = source.get_album(album_uri)
            if album != None:
                break
        request.finish(album)

    # API

    def API_modifySpotifySource(self, username, password, request):
        self.modify_spotifysource(username, password)
        request.finish()

    def API_getAllSources(self, request):
        request.finish()

    def API_search(self, query, request):
        threading.Thread(target=self.do_search, args=(query, request)).start()

    def API_getAlbums(self, query, request):
        ret = []
        for name, source in self.sources.iteritems():
            if source:
                ret += source.get_albums(query)
        request.finish(ret)

    def API_getAlbum(self, album_uri, request):
        threading.Thread(target=self.get_album,
                         args=(album_uri, request)).start()

    def API_list(self, type, request):
        ret = []
        for name, source in self.sources.itermitems():
            if source:
                ret += source.list(type)
        request.finish(ret)

    def API_getAlbumArt(self, artist, album, size, request):
        threading.Thread(target=self.fetch_albumart,
                         args=(artist, album, size, request)).start()

    def API_createPlaylist(self, name, request):
        Playlist.objects.create(name=name)
        request.finish()

    def API_removePlaylist(self, id, request):
        playlist = Playlist.objects.get(id=id)
        playlist.tracks.clear() # TODO: check this!
        playlist.delete()
        self.needs_push_update = True
        request.finish()

    def API_addTrackToPlaylist(self, playlist_id, uri, request):
        track = self.create_track_from_uri(uri)
        try:
            playlist = Playlist.objects.get(id=playlist_id)
            e = Entry.objects.create(playlist=playlist, track=track)
#        except ValueError as e:
        except:
            raise

        self.needs_push_update = True
        request.finish() # TODO: do we need to return anything here??
#        request.finish(playlist.add_track(track, 0))

    def API_addTracksToPlaylist(self, playlist_id, uri, request):
        tracks = self.create_tracks_from_uri(uri)
        try:
            playlist = Playlist.objects.get(id=playlist_id)
#        except ValueError as e:
        except:
            raise
        self.needs_push_update = True

        for track in tracks:
            Entry.objects.create(playlist=playlist, track=track)
        request.finish()
#        request.finish(playlist.add_tracks(tracks, -1))

    def API_removeTrackFromPlaylist(self, playlist_id, track_id, request):
#        try:
#            playlist = Playlist.get(playlist_id)
#            playlist.remove_playlist_tracks_id(int(track_id))
#        except ValueError as e:
#            raise
#        self.needs_push_update = True
        print "not implemented 1"
        request.finish()

    def API_removeTracksFromPlaylist(self, playlist_id, track_ids, request):
#        try:
#            playlist = Playlist.get(playlist_id)
#            for track_id in track_ids.split(','):
#                # don't crash on railing comma
#                if track_id != '':
#                    playlist.remove_playlist_tracks_id(int(track_id))
#        except ValueError as e:
#            raise
#        self.needs_push_update = True
        print "not implemented 2"
        request.finish()

    def API_getAllPlaylists(self, request):
        ps = [model_to_dict(p) for p in Playlist.objects.exclude(name=self.ampdbname+"0")]
        request.finish(ps)

    def API_getAllTracksInPlaylist(self, playlist_id, request):
        # TODO: I don't know how to join these automatically
        tracks = []
        for entry in Playlist.objects.get(id=playlist_id).entry_set.all():
            t = model_to_dict(entry.track)
            t["id"] = entry.id # use the unique id instead of track_id
            tracks.append(t)
        request.finish(tracks)

    def API_renamePlaylist(self, playlist_id, name, request):
        try:
            # TODO: is there a "update" method?
            p = Playlist.objects.get(id=playlist_id)
            p.name = name
            p.save()
        #except ValueError as e:
        except:
            raise
        self.needs_push_update = True
        request.finish()

    def API_moveTrackInPlaylist(self, playlist_id, track_id, position, request):
        e = Entry.objects.get(id=track_id)
        e.insert_at(int(position)-1)
        request.finish()

    def API_getSearchHistory(self, nbr, request):
        request.finish(self.search_history[-int(nbr):])

    def API_cleanDatabase(self, request):
        db = Database()
        db.commit_statement('''delete from votes''')
        db.commit_statement('''delete from collection''')
        db.commit_statement('''delete from users''')
        db.commit_statement('''delete from tracks''')
        db.commit_statement('''delete from playlists where id != 1''')
        db.commit_statement('''delete from entries''')
        request.finish()
