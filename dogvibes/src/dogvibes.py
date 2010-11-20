import gobject
import gst
import os
import config
import sys
import hashlib
import random
import time
import logging

import threading

# import spources
#from filesource import FileSource
#from srradiosource import SRRadioSource
#from youtubesource import YoutubeSource
from spotifysource import SpotifySource

from albumart import AlbumArt

# import speakers
from devicespeaker import DeviceSpeaker
from fakespeaker import FakeSpeaker

from models import Track
from models import Playlist
from models import User
from models import Entry
from models import Vote
from database import Database

from django.db import models
from django.db.models import Count
from django.forms.models import model_to_dict

from django.forms.models import model_to_dict

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Dogvibes():
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
        self.sources = {}

        # create gstreamer stuff
        self.pipeline = gst.Pipeline("dogvibespipeline")

        # create the tee element
        self.tee = gst.element_factory_make("tee", "tee")
        self.pipeline.add(self.tee)

        # listen for EOS
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.pipeline_message)

        # the gstreamer source that is currently used for playback
        self.src = None

        # add all speakers, should also be stored in database as sources
        self.speakers = [DeviceSpeaker("devicesink"), FakeSpeaker("fakespeaker")]
        # assume first speaker is device speaker
        self.connect_speaker(0)

        spot_user = cfg["SPOTIFY_USER"]
        spot_pass = cfg["SPOTIFY_PASS"]
        self.modify_spotifysource(spot_user, spot_pass)

        # playlist stuff
        self.vote_version = 0
        self.playlist_version = 0
        self.active_playlist = None

    def create_tracks_from_uri(self, uri):
        tracks = []
        for name,source in self.sources.iteritems():
            if source:
                tracks = source.create_tracks_from_uri(uri)
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from URI')

    def get_all_tracks_in_playlist(self, playlistid):
        try:
            playlist = Playlist.get(playlistid)
        except ValueError as e:
            raise ValueError, 'Playlist does not exist'
        tracks = playlist.get_all_tracks()
        ret = [track.__dict__ for track in tracks]
        return ret

    def do_search(self, query, request):
        ret = []

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

    def get_album(self, album_uri, request):
        album = None
        for name, source in self.sources.iteritems():
            album = source.get_album(album_uri)
            if album != None:
                break
        request.finish(album)

    def next_track(self):
        self.set_state(gst.STATE_NULL)
        track = self.fetch_active_track()
        if track == None:
            return

        self.remove_track(None, track.id, add_again=True)

        track = self.fetch_active_track()
        if track != None:
            self.start_track(track)

    def pipeline_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            logging.debug ("Song is over changing track.")
            self.next_track()
            self.playlist_version += 1
            self.vote_version += 1
            self.needs_push_update = True

    def pad_added(self, element, pad, last):
        logging.debug("Lets add a speaker we found suitable elements to decode")
        pad.link(self.tee.get_pad("sink"))

    def start_track(self, track):
        (pending, state, timeout) = self.pipeline.get_state()

        logging.debug ("Start track %s", track.uri)

        if self.src:
            self.pipeline.remove(self.src)
            if self.pipeline.get_by_name("decodebin2") != None:
                self.pipeline.remove(self.decodebin)

        self.src = None

        for key in self.sources.keys():
            if self.sources[key].uri_matches(track.uri):
                self.src = self.sources[key].get_src()
                self.sources[key].set_track(track)
                self.pipeline.add(self.src)
                self.src.link(self.tee)

        # Try decode bin if there where no match within the sources
        if self.src == None:
            logging.debug ("Decodebin is taking care of this uri")
            self.src = gst.element_make_from_uri(gst.URI_SRC, track.uri, "source")
            if self.src == None:
                logging.error("No suitable gstreamer element found for given uri")
                return False
            self.decodebin = gst.element_factory_make("decodebin2", "decodebin2")
            self.decodebin.connect('new-decoded-pad', self.pad_added)
            self.pipeline.add(self.src)
            self.pipeline.add(self.decodebin)
            self.src.link(self.decodebin)

        self.set_state(gst.STATE_PLAYING)

        return True

    def get_state(self):
        (pending, state, timeout) = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            return 'playing'
        elif state == gst.STATE_NULL:
            return 'stopped'
        else:
            return 'paused'

    def set_state(self, state):
        if self.src == None:
            # FIXME return something sweet
            return
        logging.debug("set state try: "+str(state))
        res = self.pipeline.set_state(state)
        if res != gst.STATE_CHANGE_FAILURE:
            (pending, res, timeout) = self.pipeline.get_state()
            while (res != state):
                time.sleep(0.1)
                (pending, res, timeout) = self.pipeline.get_state()
            logging.debug("set state success: "+ str(state))
        else:
            logging.warning("set state failure: "+ str(state))
        return res

    def fetch_active_playlist(self):
        if (self.active_playlist == None):
            self.active_playlist = Playlist.objects.all()[0]
        return self.active_playlist

    def fetch_active_track(self):
        playlist = self.fetch_active_playlist()
        if playlist.tracks.count() <= 0:
            return None
        return playlist.tracks.all()[0]

    def remove_track(self, playlist_id, track_id, add_again=False):
        try:
            en = Entry.objects.get(id=track_id)
            playlist = en.playlist
            track = en.track
            added = en.added
            en.delete()
            if added and add_again:
                entry = Entry(track=track, playlist=playlist, added=True)
                entry.save()
        except:
            raise ValueError, 'Track does not exist'

    def get_played_milliseconds(self):
        (pending, state, timeout) = self.pipeline.get_state ()
        if (state == gst.STATE_NULL):
            logging.debug ("getPlayedMilliseconds in state==NULL")
            return 0
        try:
             src = self.src.get_by_name("source")
             pos = (pos, form) = src.query_position(gst.FORMAT_TIME)
        except:
            pos = 0
        # We get nanoseconds from gstreamer elements, convert to ms
        return pos / 1000000

    def get_status(self):
        status = {}

        # FIXME this should be speaker specific
        status['volume'] = self.speakers[0].get_volume()

        # TODO: this is sometimes updated even though a playlist is not updated
        # due to parameters that don't result in a change
        status['playlistversion'] = self.playlist_version

        playlist = self.fetch_active_playlist()

        status['playlist_id'] = self.fetch_active_playlist().id
        status['vote_version'] = self.vote_version

        track = self.fetch_active_track()
        if track != None:
            status['uri'] = track.uri
            status['title'] = track.title
            status['artist'] = track.artist
            status['album'] = track.album
            status['duration'] = int(track.duration)
            status['elapsedmseconds'] = self.get_played_milliseconds()
            status['id'] = 0 #self.active_playlists_track_id
            # TODO: Bad, bad...
            status['index'] = 0 #Entry.objects.get(id=self.active_playlists_track_id).position
        else:
            status['uri'] = "dummy"

        (pending, state, timeout) = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            status['state'] = 'playing'
        elif state == gst.STATE_NULL:
            status['state'] = 'stopped'
        else:
            status['state'] = 'paused'

        return status

    def track_to_client(self):
        track = self.fetch_active_track()
        if track == None:
            return []
        t = model_to_dict(track)
        t["id"] = self.active_playlists_track_id
        return t

    def sort_playlist(self, playlist):
        playing = playlist.entry_set.all()[0]
        for i, e in enumerate(playlist.entry_set.annotate(num_votes=Count('vote')).order_by('-num_votes', 'created_at')):
            e.position = i
            print model_to_dict(e)
            e.save()

        # If we'e playing, move that track to the top again
        if self.get_state() == "playing":
            playing.insert_at(0)

    # API

    # PLAYSLIST STUFF BEGINS HERE -------------------------------------------------

    def API_vote(self, uri, playlistid, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.create_tracks_from_uri(uri)[0]
        try:
            playlist = Playlist.objects.get(id=playlistid)
        except:
            raise ValueError, 'Playlist does not exist'

        # Get the first matching track if several with the same URI
        matching_tracks = playlist.tracks.filter(uri=uri)
        if not matching_tracks:
            entry = Entry(track=track, playlist=playlist)
        else:
            entry = matching_tracks[0].entry_set.get()

        if user.votes_left() < 1:
            logging.debug("No more votes left for %s" % user.username)
            request.finish(error = 3)
            return
        if user.already_voted(entry):
            logging.debug("%s already voted for track, ignoring" % user.username)
            request.finish(error = 3)
            return

        entry.save()

        if entry.position == 0 and self.get_state() == "playing":
            logging.debug("Can't vote for playing track")
            request.finish(error = 3)
            return

        # This is the actual voting
        Vote.objects.create(entry=entry, user=user)

        self.sort_playlist(playlist)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_unvote(self, playlistid, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.create_tracks_from_uri(uri)[0]
        playlist = Playlist.objects.get(id=playlistid)

        # Get the first matching track if several with the same URI
        # NOTE: this will possibly choose the wrong track if several tracks
        # with the same URI are in the list
        matching_tracks = playlist.tracks.filter(uri=uri)
        if not matching_tracks:
            entry = Entry.objects.create(track=track, playlist=playlist)
        else:
            entry = matching_tracks[0].entry_set.get()

        if entry.position == 0 and self.get_state() == "playing":
            logging.debug("Can't remove vote for playing track")
            request.finish(error = 3)
            return

        # Remove vote
        entry.vote_set.filter(user=user).delete()
        self.sort_playlist(playlist)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_addtrack(self, playlistid, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.create_tracks_from_uri(uri)[0]
        try:
            playlist = Playlist.objects.get(id=playlistid)
        except:
            raise ValueError, 'Playlist does not exist'

        # Get the first matching track if several with the same URI
        matching_tracks = playlist.tracks.filter(uri=uri)
        if not matching_tracks:
            entry = Entry(track=track, playlist=playlist, added=True)
            entry.save()
        else:
            raise ValueError, 'Track already exists in playlist'

        self.sort_playlist(playlist)
        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removetrack(self, playlistid, track_id, request):
        track_id = int(track_id)
        self.remove_track(playlistid, track_id)
        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_addplaylist(self, name, request):
        Playlist.objects.create(name=name)
        request.finish()

    def API_remove(self, playlistid, request):
        try:
            playlist = Playlist.objects.get(id=playlistid)
        except:
            raise ValueError, 'Playlist does not exist'

        if (playlist.id == self.fetch_active_playlist().id):
            raise ValueError, 'Not allowed to remove active playlist'

        playlist.tracks.clear()
        playlist.delete()
        self.needs_push_update = True
        request.finish()

    def API_playlists(self, request):
        ps = [model_to_dict(p) for p in Playlist.objects.all()]
        request.finish(ps)

    def API_setactive(self, playlistid, request):
        try:
            ps = Playlist.objects.get(id=playlistid)
        except:
            raise ValueError, 'Playlist does not exist'

        # stop playback when list is changed
        if ps != self.active_playlist:
            self.set_state(gst.STATE_NULL)
            request.push({'state': 'stopped'})
            self.active_playlist = ps
        request.finish()

    def API_tracks(self, playlistid, request):
        # TODO: I don't know how to join these automatically
        tracks = []

        try:
            playlists = Playlist.objects.get(id=playlistid).entry_set.all().annotate(votes=Count('vote'))
        except:
            raise ValueError, "Playlist does not exist"

        for entry in playlists:
            t = model_to_dict(entry.track)
            t["id"] = entry.id # use the unique id instead of track_id
            t["votes"] = entry.votes
            tracks.append(t)
        request.finish(tracks)

    def API_rename(self, playlistid, name, request):
        try:
            p = Playlist.objects.get(id=playlistid)
            p.name = name
            p.save()
        except:
            raise ValueError, 'Playlist does not exist'
        self.needs_push_update = True
        request.finish()

    def API_list(self, request):
        print "please implement me"
        request.finish()

    # PLAYSLIST STUFF ENDS HERE -------------------------------------------------

    # SKIPPING AND JUMPING STUFF STARTS HERE -------------------------------------------------

    def API_seek(self, mseconds, request):
        if self.src == None:
            request.finish(0)
        ns = int(mseconds) * 1000000
        logging.debug("Seek with time to ns=%d" %ns)
        self.pipeline.seek_simple (gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, ns)
        request.push({'duration': self.fetch_active_track().duration})
        request.finish()

    def API_play(self, request):
        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()
        if track != None:
            self.start_track(track)
            self.set_state(gst.STATE_PLAYING)

        request.push({'state': self.get_state()})
        request.finish()

    def API_stop(self, request):
        self.set_state(gst.STATE_NULL)
        request.push({'state': 'stopped'})
        request.finish()

    def API_pause(self, request):
        self.set_state(gst.STATE_PAUSED)
        # FIXME we need to push the state paused to all clients
        # when play token lost, request == None
        if request != None:
            request.push({'state': self.get_state()})
            request.finish()

    def API_next(self, request):
        self.next_track()
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_id': self.fetch_active_playlist().id})
        request.push({'state': self.get_state()})
        request.finish()

    # SKIPPING AND JUMPING STUFF ENDS HERE -------------------------------------------------

    # STATUS STUFF STARTS HERE -------------------------------------------------

    def API_playedmilliseconds(self, request):
        request.finish(self.get_played_milliseconds())

    def API_status(self, request):
        request.finish(self.get_status())

    def API_volume(self, level, request):
        level = float(level)
        if (level > 1.0 or level < 0.0):
            raise ValueError, 'Volume must be between 0.0 and 1.0'
        self.speakers[0].set_volume(level)
        request.push({'volume': self.speakers[0].get_volume()})
        request.finish()

    def API_getActivity(self, limit, request):
        activities = []
        for v in Vote.objects.all()[0:int(limit)]:
            a = model_to_dict(v.user)
            a.update(model_to_dict(v.entry.track))
            a["id"] = v.entry.id
            a["time"] = time.mktime(time.strptime(v.created_at.split(".")[0], "%Y-%m-%d %H:%M:%S"))
            activities.append(a)
        request.finish(activities)

    def API_info(self, request):
        user, created = User.objects.get_or_create(username=request.user,
                                                   defaults={'avatar_url': request.avatar_url})
        ret = model_to_dict(user)
        ret["votes"] = user.votes_left()
        voted_tracks = []
        for vote in user.vote_set.all():
            track = model_to_dict(vote.entry.track)
            track["id"] = vote.entry.id
            voted_tracks.append(track)
        ret["voted_tracks"] = voted_tracks
        request.finish(ret)

    # STATUS STUFF ENDS HERE -------------------------------------------------

    # ALBUM STUFF STARTS HERE -------------------------------------------------

    def API_getAlbums(self, query, request):
        ret = []
        for name, source in self.sources.iteritems():
            if source:
                ret += source.get_albums(query)
        request.finish(ret)

    def API_getAlbum(self, album_uri, request):
        threading.Thread(target=self.get_album,
                         args=(album_uri, request)).start()

    def API_getAlbumArt(self, artist, album, size, request):
        threading.Thread(target=self.fetch_albumart,
                         args=(artist, album, size, request)).start()

    # ALBUM STUFF ENDS HERE -------------------------------------------------

    # SEARCH STUFF STARTS HERE  -------------------------------------------------

    def API_search(self, q, request):
        threading.Thread(target=self.do_search, args=(q, request)).start()

    def API_getSearchHistory(self, nbr, request):
        request.finish(self.search_history[-int(nbr):])

    # SEARCH STUFF ENDS HERE  -------------------------------------------------

    # DEBUG STUFF STARTS HERE -------------------------------------------------

    def API_cleandatabase(self, request):
        db = Database()
        db.commit_statement('''delete from votes''')
        db.commit_statement('''delete from collection''')
        db.commit_statement('''delete from users''')
        db.commit_statement('''delete from tracks''')
        db.commit_statement('''delete from playlists''')
        db.commit_statement('''delete from entries''')
        request.finish()

    # DEBUG STUFF ENDS HERE -------------------------------------------------

    # MISC SOURCE STUFF STARTS HERE -------------------------------------------------

    def connect_speaker(self, nbr, request = None):
        nbr = int(nbr)
        if nbr > len(self.speakers) - 1:
            logging.warning("Connect speaker - speaker does not exist")

        speaker = self.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) == None:
            self.sink = self.speakers[nbr].get_speaker()
            self.pipeline.add(self.sink)
            self.tee.link(self.sink)
        else:
            logging.debug("Speaker %d already connected" % nbr)

    def modify_spotifysource(self, username, password):
        if self.sources.has_key("spotify"):
            self.sources["spotify"].relogin(username, password)
        else:
            spotifysource = SpotifySource("spotify", username, password)
            self.sources["spotify"] = spotifysource

    def API_connectSpeaker(self, nbr, request):
        self.connect_speaker(nbr)
        request.finish()

    def API_disconnectSpeaker(self, nbr, request):
        nbr = int(nbr)
        if nbr > len(self.speakers) - 1:
            logging.warning("disconnect speaker - speaker does not exist")

        speaker = self.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) != None:
            (pending, state, timeout) = self.pipeline.get_state()
            self.set_state(gst.STATE_NULL)
            rm = self.pipeline.get_by_name(speaker.name)
            self.pipeline.remove(rm)
            self.tee.unlink(rm)
            self.set_state(state)
        else:
            logging.warning ("disconnect speaker - speaker not found")
        request.finish()

    def API_modifySpotifySource(self, username, password, request):
        self.modify_spotifysource(username, password)
        request.finish()

    # MISC SOURCE STUFF ENDS HERE -------------------------------------------------
