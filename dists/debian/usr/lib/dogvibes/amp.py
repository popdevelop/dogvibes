import gst
import hashlib
import random
import config

from track import Track
from playlist import Playlist

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Amp():
    def __init__(self, dogvibes, id):
        cfg = config.load("/etc/dogvibes.conf")
        self.dogvibes = dogvibes
        self.pipeline = gst.Pipeline ("amppipeline")

        # create the tee element
        self.tee = gst.element_factory_make("tee", "tee")
        self.pipeline.add(self.tee)

        # listen for EOS
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.pipeline_message)

        self.playqueue = []
        self.inplayqueue = False

        # create a playlist if there aren't any
        # TODO: not necessary when playback from search results is permitted
        playlist_name = "Initial"
        if (Playlist.get_all() == []):
            Playlist.create(playlist_name)
            playlist = Playlist.get_by_name(playlist_name)
        else:
            playlist = Playlist.get_all()[0]
        self.active_playlist_id = playlist.id
        self.active_playlist_position = 0

        self.src = None

        # set playlist mode to normal
        self.playlist_mode = "normal"
        if("ENABLE_SPOTIFY_SOURCE" in cfg):
            # spotify is special FIXME: not how its supposed to be
            self.spotify = self.dogvibes.sources[0].get_src()
            self.spotify.get_by_name("spot").connect('play-token-lost', self.play_token_lost)

    # API

    def API_connectSpeaker(self, nbr):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            print "Speaker does not exist"

        speaker = self.dogvibes.speakers[nbr];

        if self.pipeline.get_by_name(speaker.name) == None:
            self.sink = self.dogvibes.speakers[nbr].get_speaker();
            self.pipeline.add(self.sink)
            self.tee.link(self.sink)
        else:
            print "Speaker %d already connected" % nbr

    def API_disconnectSpeaker(self, nbr):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            print "Speaker does not exist"

        speaker = self.dogvibes.speakers[nbr];

        if self.pipeline.get_by_name(speaker.name) != None:
            (pending, state, timeout) = self.pipeline.get_state()
            self.pipeline.set_state(gst.STATE_NULL)
            rm = self.pipeline.get_by_name(speaker.name)
            self.pipeline.remove(rm)
            self.tee.unlink(rm)
            self.pipeline.set_state(state)
        else:
            print "Speaker not connected"

    def API_getAllTracksInQueue(self):
        return [track.__dict__ for track in self.playqueue]

    def API_getPlayedMilliSeconds(self):
        (pending, state, timeout) = self.pipeline.get_state ()
        if (state == gst.STATE_NULL):
            return 0
        (pos, form) = self.pipeline.query_position(gst.FORMAT_TIME)
        return pos / 1000 # / gst.MSECOND # FIXME: something fishy here...

    def API_getStatus(self):
        status = {}

        # FIXME this should be speaker specific
        status['volume'] = self.dogvibes.speakers[0].get_volume()
        status['playqueuehash'] = self.get_hash_from_play_queue()

        track = None

        if self.inplayqueue:
            if len(self.playqueue) > 0:
                track = self.playqueue[0]
        else:
            playlist = Playlist.get(self.active_playlist_id)
            if self.active_playlist_id != -1 and playlist.length() > 0:
                track = playlist.get_track_nbr(self.active_playlist_position)

        status['uri'] = "dummy"

        if track != None:
            status['uri'] = track.uri
            status['title'] = track.title,
            status['artist'] = track.artist,
            status['album'] = track.album,
            status['duration'] = int(track.duration),
            status['elapsedmseconds'] = self.API_getPlayedMilliSeconds()

        status['index'] = self.active_playlist_position

        print self.active_playlist_position

        (pending, state, timeout) = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            status['state'] = 'playing'
        elif state == gst.STATE_NULL:
            status['state'] = 'stopped'
        else:
            status['state'] = 'paused'

        return status

    def API_getQueuePosition(self):
        return self.active_playlist_position

    def API_nextTrack(self):
        if (len(self.playqueue) > 0 and self.inplayqueue):
            self.playqueue.remove(self.playqueue[0])

        if (len(self.playqueue) > 0):
            self.inplayqueue = True
            (pending, state, timeout) = self.pipeline.get_state()
            self.pipeline.set_state(gst.STATE_NULL)
            self.play_only_if_null(self.playqueue[0])
            self.pipeline.set_state(state)
        else:
            self.change_track(self.active_playlist_position + 1)

    def API_playTrack(self, nbr):
        self.change_track(nbr)
        self.API_play()

    def API_playQueueTrack(self, nbr):
        if (nbr > (len(self.playqueue) - 1)):
            raise DogError, 'Trying to remove none existsing track from playqueue'
        self.inplayqueue = True

        for i in range(0, nbr):
            self.playqueue.remove(self.playqueue[0])

        self.API_play()

    def API_previousTrack(self):
        # TODO: stay on same place if in play queue?
        if (self.inplayqueue):
            self.change_track(self.active_playlist_position)
        else:
            self.change_track(self.active_playlist_position - 1)

    def API_play(self):
        if (len(self.playqueue) > 0 and (self.inplayqueue or self.active_playlist_id == -1)):
            self.inplayqueue = True
            self.play_only_if_null(self.playqueue[0])
        else:
            playlist = Playlist.get(self.active_playlist_id)
            if self.active_playlist_id == -1:
                pass
            elif self.active_playlist_position > playlist.length() - 1:
                raise DogError, 'Trying to play an empty playqueue'
            else:
                self.play_only_if_null(playlist.get_track_nbr(self.active_playlist_position))

    def API_pause(self):
        self.pipeline.set_state(gst.STATE_PAUSED)

    def API_queue(self, uri):
        self.inplayqueue = True
        track = self.dogvibes.create_track_from_uri(uri)
        self.playqueue.append(track)

    def API_removeTrack(self, nbr):
        nbr = int(nbr)
        if nbr > len(self.playqueue):
            raise DogError, 'Track not removed, playqueue is not that big'
        self.playqueue.remove(self.playqueue[nbr])

    def API_seek(self, mseconds):
        print "Seek simple to " + mseconds + " useconds"
         # FIXME: this *1000-hack only works for Spotify?
        self.pipeline.seek_simple (gst.FORMAT_TIME, gst.SEEK_FLAG_NONE, int(mseconds) * 1000);
        self.src.get_pad("src").push_event(gst.event_new_flush_start())
        self.src.get_pad("src").push_event(gst.event_new_flush_stop())

    def API_setPlayList(self, id, position):
        self.active_playlist_id = id
        self.active_playlist_position = position

    def API_setPlayQueueMode(self, mode):
        if (mode != "normal" and mode != "random" and mode != "repeat" and mode != "repeattrack"):
            raise DogError, "Unknown playqueue mode:" + mode
        self.playlist_mode = mode

    def API_setVolume(self, level):
        level = float(level)
        if (level > 1.0 or level < 0.0):
            raise DogError, 'Volume must be between 0.0 and 1.0'
        self.dogvibes.speakers[0].set_volume(level)

    def API_stop(self):
        self.pipeline.set_state(gst.STATE_NULL)

    # Internal functions

    def pad_added(self, element, pad, last):
        print "Lets add a speaker we found suitable elements to decode"
        pad.link(self.tee.get_pad("sink"))

    def change_track(self, tracknbr):
        tracknbr = int(tracknbr)

        self.inplayqueue = False

        playlist = Playlist.get(self.active_playlist_id)

        if playlist == None:
            self.pipeline.set_state(gst.STATE_NULL)
            return
        elif (self.playlist_mode == "random"):
            self.active_playlist_position = random.randint(0, playlist.length() - 1)
        elif (self.playlist_mode == "repeattrack"):
            pass
        elif (tracknbr >= 0) and (tracknbr < playlist.length()):
            self.active_playlist_position = tracknbr
        elif tracknbr < 0:
            self.active_playlist_position = 0
        elif (tracknbr >= playlist.length()) and (self.playlist_mode == "repeat"):
            self.active_playlist_position = 0
        else:
            self.active_playlist_position = (playlist.length() - 1)
            self.pipeline.set_state(gst.STATE_NULL)
            return

        (pending, state, timeout) = self.pipeline.get_state()
        self.pipeline.set_state(gst.STATE_NULL)

        self.play_only_if_null(playlist.get_track_nbr(self.active_playlist_position))
        self.pipeline.set_state(state)

    def get_hash_from_play_queue(self):
        ret = "dummy"
        for track in self.playqueue:
            ret += track.uri
        return hashlib.md5(ret).hexdigest()

    def pipeline_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.API_nextTrack()

    def play_only_if_null(self, track):
        (pending, state, timeout) = self.pipeline.get_state()
        if state != gst.STATE_NULL:
            self.pipeline.set_state(gst.STATE_PLAYING)
            return

        if self.src:
            self.pipeline.remove(self.src)
            if self.spotify_in_use == False:
                self.pipeline.remove(self.decodebin)

        if track.uri[0:7] == "spotify":
            self.src = self.spotify
            # FIXME ugly
            self.dogvibes.sources[0].set_track(track)
            self.pipeline.add(self.src)
            self.src.link(self.tee)
            self.spotify_in_use = True
        else:
            print "Decodebin is taking care of this uri"
            self.src = gst.element_make_from_uri(gst.URI_SRC, track.uri, "source")
            self.decodebin = gst.element_factory_make("decodebin2", "decodebin2")
            self.decodebin.connect('new-decoded-pad', self.pad_added)
            self.pipeline.add(self.src)
            self.pipeline.add(self.decodebin)
            self.src.link(self.decodebin)
            self.spotify_in_use = False

        self.pipeline.set_state(gst.STATE_PLAYING)

    def play_token_lost(self, data):
        self.API_pause()
