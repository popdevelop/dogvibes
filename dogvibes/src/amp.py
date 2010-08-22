import gst
import hashlib
import random
import time
import logging
import shelve

from models import Track
from models import Playlist
from models import Entry
from models import User
from models import Vote

from django.db import models
from django.db.models import Count
from django.forms.models import model_to_dict

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Amp():
    def __init__(self, dogvibes, id):
        self.dogvibes = dogvibes
        self.pipeline = gst.Pipeline("amppipeline" + id)

        # create the tee element
        self.tee = gst.element_factory_make("tee", "tee")
        self.pipeline.add(self.tee)

        # listen for EOS
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.pipeline_message)

        # Create amps playqueue
        try:
            tqplaylist = Playlist.objects.get(name=dogvibes.ampdbname + id)
        except Playlist.DoesNotExist as e:
            tqplaylist = Playlist.objects.create(name=dogvibes.ampdbname + id)
        self.tmpqueue_id = tqplaylist.id

        # These should be objects instead of indices
        self.active_playlist_id = self.tmpqueue_id
        self.active_playlists_track_id = -1
        self.fallback_playlist_id = -1
        self.fallback_playlists_track_id = -1

        self.vote_version = 0
        self.playlist_version = 0

        # sources connected to the amp
        self.sources = shelve.open("amp" + id + ".shelve", writeback=True)

        # aquire all sources
        for key in self.sources.keys():
            self.dogvibes.sources[key].amp = self

        # the gstreamer source that is currently used for playback
        self.src = None

        logging.debug("Initiated amp %s", id)

        self.needs_push_update = False

    # Soon to be API
    def connect_source(self, name):
        if not self.dogvibes.sources.has_key(name):
            logging.warning ("Connect source - source does not exist")
            return

        if self.dogvibes.sources[name].amp != None:
            logging.warning ("Connect source - source is already connected to amp")
            return

        # Add amp as owner of source
        self.dogvibes.sources[name].amp = self
        self.sources[name] = name
        self.sources.sync()

    def disconnect_source(self, name):
        if not self.dogvibes.sources.has_key(name):
            logging.warning ("Connect source - source does not exist")
            return

        if self.dogvibes.sources[name].amp == None:
            logging.warning ("Source has no owner")
            return

        if self.dogvibes.sources[name].amp != self:
            logging.warning ("Amp not owner of this source")
            return

        del self.sources[name]
        self.sources.sync()

    def connect_speaker(self, nbr, request = None):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            logging.warning("Connect speaker - speaker does not exist")

        speaker = self.dogvibes.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) == None:
            self.sink = self.dogvibes.speakers[nbr].get_speaker()
            self.pipeline.add(self.sink)
            self.tee.link(self.sink)
        else:
            logging.debug("Speaker %d already connected" % nbr)
        #self.needs_push_update = True
        # FIXME: activate when client connection has been fixed!

    def pad_added(self, element, pad, last):
        logging.debug("Lets add a speaker we found suitable elements to decode")
        pad.link(self.tee.get_pad("sink"))

    def change_track(self, tracknbr, relative):
        tracknbr = int(tracknbr)

        logging.debug("Change to track %d, is relative:%d", tracknbr, relative)

        if relative and (tracknbr > 1 or tracknbr < -1):
            raise DogError, "Relative change track greater/less than 1 not implemented"

        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()

        if track == None and relative:
            logging.warning("I am lost can not call relative because i do no know where I am")
            return

        # If we are in tmpqueue either removetrack or push it to the top
        if self.is_in_tmpqueue():
            if relative and (tracknbr == 1):
                # Remove track and goto next track
                Entry.objects.get(id=self.active_playlists_track_id).delete()
                next_position = 0
            elif relative and (tracknbr == -1):
                # Do nothing since we are always on top in playqueue
                return
            else:
                # Move requested track to top of tmpqueue and play it
                self.active_playlists_track_id = tracknbr
                #playlist.move_track(self.active_playlists_track_id, 1)
                Entry.objects.get(id=self.active_playlists_track_id).insert_at(0)
                next_position = 0

            # Check if tmpqueue no longer exists (all tracks has been removed)
            if playlist.tracks.count() <= 0:
                # Check if we used to be in a playlist
                if self.fallback_playlist_id != -1:
                    # Change one track forward in the playlist we used to be in
                    self.active_playlist_id = self.fallback_playlist_id
                    self.active_playlists_track_id = self.fallback_playlists_track_id
                    playlist = Playlist.objects.get(id=self.active_playlist_id)
                    next_position = Entry.objects.get(id=self.active_playlists_track_id).position
                    next_position = next_position + 1
                    if next_position >= playlist.tracks.count():
                        # We were the last song in the playlist we used to be in, just stop everyting
                        self.set_state(gst.STATE_NULL)
                        return
                else:
                    # We have not entered any playlist yet, just stop playback
                    self.set_state(gst.STATE_NULL)
                    return
        elif (Playlist.objects.get(id=self.tmpqueue_id).tracks.count() > 0) and relative:
            # Save the playlist that we curently are playing in for later use
            self.fallback_playlist_id = self.active_playlist_id
            self.fallback_playlists_track_id = self.active_playlists_track_id
            # Switch to playqueue
            self.active_playlist_id = self.tmpqueue_id
            playlist = Playlist.objects.get(id=self.active_playlist_id)
            next_position = 0
        else:
            # We are inside a playlist
            if relative:
                next_position = Entry.objects.get(id=self.active_playlists_track_id).position + tracknbr
            else:
#                try:
                    next_position = Entry.objects.get(id=tracknbr).position
                    logging.debug("In a playlist trying position %d" % next_position)
 #               except:
 #                   logging.debug("Could not find this position in the active playlist, no action")
 #                   return
        try:
            entry = playlist.entry_set.all()[next_position]
        except:
            self.set_state(gst.STATE_NULL)
            self.active_playlists_track_id = -1
            logging.debug("Could not get to next positon in the active playlist")
            return

        self.active_playlists_track_id = entry.id
        self.set_state(gst.STATE_NULL)
        self.start_track(entry.track)

    def pipeline_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.next_track()
            #request.push({'state': self.get_state()})
            #request.push(self.track_to_client())
            self.vote_version += 1
            self.needs_push_update = True
            # TODO: is this enough? An update is pushed to the clients
            # but will the info be correct?


    def start_track(self, track):
        (pending, state, timeout) = self.pipeline.get_state()

        logging.debug ("Start track %s", track.uri)

        if self.src:
            self.pipeline.remove(self.src)
            if self.pipeline.get_by_name("decodebin2") != None:
                self.pipeline.remove(self.decodebin)

        self.src = None

        for key in self.sources.keys():
            if self.dogvibes.sources[key].uri_matches(track.uri):
                self.src = self.dogvibes.sources[key].get_src()
                self.dogvibes.sources[key].set_track(track)
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

    def is_in_tmpqueue(self):
        return (self.tmpqueue_id == self.active_playlist_id)

    def fetch_active_playlist(self):
        try:
            playlist = Playlist.objects.get(id=self.active_playlist_id)
            return playlist
        except:
            # The play list have been removed or disapperd use tmpqueue as fallback
            self.active_playlist_id = self.tmpqueue_id
            self.active_playlists_track_id = -1
            playlist = Playlist.objects.get(id=self.active_playlist_id)
            return playlist

    def fetch_active_track(self):

        # Assume that fetch active playlist alreay been run
        playlist = Playlist.objects.get(id=self.active_playlist_id)

        if playlist.tracks.count() <= 0:
            return None

        if self.active_playlists_track_id != -1:
            try:
                logging.debug("Fetching active track, %d on playlist %d", self.active_playlists_track_id, self.active_playlist_id)
                return Entry.objects.get(id=self.active_playlists_track_id).track
            except:
                logging.debug("...but failed")
                self.active_playlists_track_id = -1
                return None
        else:
            # Try the first active_play_list id
            entry = playlist.entry_set.all()[0]
            self.active_playlists_track_id = entry.id

            if self.start_track(entry.track) == False:
                self.active_playlists_track_id = -1
                return None

            self.set_state(gst.STATE_PAUSED)
            return entry.track

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

    def next_track(self):
        self.change_track(1, True)

    def get_active_playlist_id(self):
        if self.is_in_tmpqueue():
            return -1
        else:
            return self.active_playlist_id

    def get_status(self):
        status = {}

        # FIXME this should be speaker specific
        status['volume'] = self.dogvibes.speakers[0].get_volume()

        # TODO: this is sometimes updated even though a playlist is not updated
        # due to parameters that don't result in a change
        status['playlistversion'] = self.playlist_version

        playlist = self.fetch_active_playlist()

        # -1 is in tmpqueue
        status['playlist_id'] = self.get_active_playlist_id()
        status['vote_version'] = self.vote_version

        track = self.fetch_active_track()
        if track != None:
            status['uri'] = track.uri
            status['title'] = track.title
            status['artist'] = track.artist
            status['album'] = track.album
            status['duration'] = int(track.duration)
            status['elapsedmseconds'] = self.get_played_milliseconds()
            status['id'] = self.active_playlists_track_id
            # TODO: Bad, bad...
            status['index'] = Entry.objects.get(id=self.active_playlists_track_id).position
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

    def play_track(self, playlist_id, nbr):
        nbr = int(nbr)
        playlist_id = int(playlist_id) # TODO: should extract this from track

        logging.debug("Playing track %d on playlist %d", nbr, playlist_id)

        # -1 is tmpqueue
        if playlist_id == -1:
            # Save last known playlist that is not the tmpqueue
            if (not self.is_in_tmpqueue()):
                self.fallback_playlist_id = self.active_playlist_id
                self.fallback_playlists_track_id = self.active_playlists_track_id
            self.active_playlist_id = self.tmpqueue_id
        else:
            logging.debug("Setting active playlist %d", playlist_id)
            self.active_playlist_id = playlist_id

        self.change_track(nbr, False)

    def stop(self):
        self.set_state(gst.STATE_NULL)

    # API

    def API_connectSource(self, name, request):
        self.connect_source(name)
        request.finish(name)

    def API_disconnectSource(self, name, request):
        self.disconnect_source(name)
        request.finish(name)

    def API_connectSpeaker(self, nbr, request):
        self.connect_speaker(nbr)
        request.finish()

    def API_disconnectSpeaker(self, nbr, request):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            logging.warning ("disconnect speaker - speaker does not exist")

        speaker = self.dogvibes.speakers[nbr]

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

    def API_getAllTracksInQueue(self, request):
        # TODO: I don't know how to join these automatically
        tracks = []
        for entry in Playlist.objects.get(id=self.tmpqueue_id).entry_set.all().annotate(votes=Count('vote')):
            t = model_to_dict(entry.track)
            t["id"] = entry.id # use the unique id instead of track id
            t["votes"] = entry.votes # TODO: remove
            t["voters"] = [model_to_dict(v.user) for v in entry.vote_set.select_related()]
            tracks.append(t)
        request.finish(tracks)

    def API_getPlayedMilliSeconds(self, request):
        request.finish(self.get_played_milliseconds())

    def API_getStatus(self, request):
        request.finish(self.get_status())

    def API_nextTrack(self, request):
        self.next_track()
        self.playlist_version += 1
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_playTrack(self, playlist_id, nbr, request):
        self.play_track(playlist_id, nbr)
        self.playlist_version += 1
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_previousTrack(self, request):
        self.change_track(-1, True)
        self.playlist_version += 1
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_play(self, request):
        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()
        if track != None:
            self.set_state(gst.STATE_PLAYING)

        request.push({'state': self.get_state()})
        request.finish()

    def API_pause(self, request):
        self.set_state(gst.STATE_PAUSED)
        # FIXME we need to push the state paused to all clients
        # when play token lost, request == None
        if request != None:
            request.push({'state': self.get_state()})
            request.finish()

    def sort_playlist(self, playqueue):
        # Sort tracks in playqueue on number of votes and creation time
        if self.get_state() == gst.STATE_PLAYING:
            playing = playqueue.entry_set.all()[0]
        for i, e in enumerate(playqueue.entry_set.annotate(num_votes=Count('vote')).order_by('-num_votes', 'created_at')):
            e.position = i
            e.save()
        # If we'e playing, move that track to the top again
        if self.get_state() == gst.STATE_PLAYING:
            playing.insert_at(0)


    # TODO: addVote should exist in two modes, adding a URI from search and
    # voting for a specific entry in the playqueue.
    def API_addVote(self, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.dogvibes.create_track_from_uri(uri)
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)

        if user.votes_left() < 1:
            logging.debug("No more votes left for %s" % user.username)
            request.finish(error = 3)
            return
        if user.already_voted(track):
            logging.debug("%s already voted for track, ignoring" % user.username)
            request.finish(error = 3)
            return

        # Get the first matching track if several with the same URI
        matching_tracks = playqueue.tracks.filter(uri=uri)
        if not matching_tracks:
            track = self.dogvibes.create_track_from_uri(uri)
            entry = Entry.objects.create(track=track, playlist=playqueue)
        else:
            entry = matching_tracks[len(matching_tracks)-1].entry_set.get()

        # This is the actual voting
        Vote.objects.create(entry=entry, user=user)

        self.sort_playlist(playqueue)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removeVote(self, uri, request):
        user, created = User.objects.get_or_create(username=request.user, defaults={'avatar_url': request.avatar_url})
        track = self.dogvibes.create_track_from_uri(uri)
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)

        # Get the first matching track if several with the same URI
        # NOTE: this will possibly choose the wrong track if several tracks
        # with the same URI are in the list
        matching_tracks = playqueue.tracks.filter(uri=uri)
        if not matching_tracks:
            track = self.dogvibes.create_track_from_uri(uri)
            entry = Entry.objects.create(track=track, playlist=playqueue)
        else:
            entry = matching_tracks[len(matching_tracks)-1].entry_set.get()

        # Remove vote
        entry.vote_set.filter(user=user).delete()

        self.sort_playlist(playqueue)

        self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'playlist_version': self.playlist_version})
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_queue(self, uri, request):
        playqueue = Playlist.objects.get(id=self.tmpqueue_id)
        tracks = self.dogvibes.create_tracks_from_uri(uri)
        [Entry.objects.create(playlist=playqueue, track=track) for track in tracks]

        self.playlist_version += 1
        self.needs_push_update = True
        request.finish()

    def API_queueAndPlay(self, uri, request):
        # If in tmpqueue and state is playing and there are tracks in tmpqueue.
        # Then remove the currently playing track. Since we do not want to queue tracks
        # from just "clicking around".
        playlist = Playlist.objects.get(id=self.active_playlist_id)
        if self.is_in_tmpqueue() and self.get_state() == 'playing' and playlist.tracks.count() >= 1:
            playlist.entry_set.all()[0].delete()

        tracks = self.dogvibes.create_tracks_from_uri(uri)
        e = None
        queue = Playlist.objects.get(id=self.tmpqueue_id)
        for track in tracks:
            e = Entry(playlist=queue, track=track)
            e.insert_at(0)
        self.play_track(queue.id, e.id)

        self.playlist_version += 1
        self.needs_push_update = True
        request.finish()

    def API_removeTrack(self, track_id, request):
        track_id = int(track_id)

        # For now if we are trying to remove the existing playing track. Do nothing.
        if (track_id == self.active_playlist_id):
            logging.warning("Not allowed to remove playing track")
            request.finish(error = 3)
            return

        Entry.objects.get(id=track_id).delete()
        self.needs_push_update = True

        self.playlist_version += 1
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removeTracks(self, track_ids, request):
        for track_id in track_ids.split(','):
            # don't crash on trailing comma
            if track_id != '':
                track_id = int(track_id)

                # For now if we are trying to remove the existing playing track. Do nothing.
                if (track_id == self.active_playlist_id):
                    logging.warning("Not allowed to remove playing track")
                    continue

                playlist = Playlist.get(self.tmpqueue_id)
                playlist.remove_playlist_tracks_id(track_id)
                self.needs_push_update = True
        self.playlist_version += 1
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_seek(self, mseconds, request):
        if self.src == None:
            request.finish(0)
        ns = int(mseconds) * 1000000
        logging.debug("Seek with time to ns=%d" %ns)
        self.pipeline.seek_simple (gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, ns)
        request.push({'duration': self.fetch_active_track().duration})
        request.finish()

    def API_setVolume(self, level, request):
        level = float(level)
        if (level > 1.0 or level < 0.0):
            raise DogError, 'Volume must be between 0.0 and 1.0'
        self.dogvibes.speakers[0].set_volume(level)
        request.push({'volume': self.dogvibes.speakers[0].get_volume()})
        request.finish()

    def API_stop(self, request):
        self.set_state(gst.STATE_NULL)
        request.push({'state': 'stopped'})
        request.finish()

    def API_getActivity(self, limit, request):
        activities = []
        for v in Vote.objects.all()[0:int(limit)]:
            a = model_to_dict(v.user)
            a.update(model_to_dict(v.user))
            a.update(model_to_dict(v.entry.track))
            a["id"] = v.entry.id
            activities.append(a)
        request.finish(activities)

    def API_getUserInfo(self, request):
        user, created = User.objects.get_or_create(username=request.user,
                                                   defaults={'avatar_url': request.avatar_url})
        ret = model_to_dict(user)
        ret["votes"] = user.vote_set.count()
        request.finish(ret)
