import gst
#import spotifydogvibes

import urllib
import xml.etree.ElementTree as ET

from track import Track

class SpotifySource:
    def __init__(self, name, user, passw):
        self.name = name
        self.passw = passw
        self.user = user
        self.created = False
        #spotifydogvibes.login(user, passw);

    def create_track_from_uri(self, uri):
        url = "http://ws.spotify.com/lookup/1/?uri=" + uri

        try:
            e = ET.parse(urllib.urlopen(url))
        except Exception as e:
            return None

        ns = "http://www.spotify.com/ns/music/1"

        title = e.find('.//{%s}name' % ns).text
        artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
        album = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
        duration = int(float(e.find('.//{%s}length' % ns).text))

        track = Track(uri)
        track.title = title
        track.artist = artist
        track.album = album
        track.duration = duration

        return track

    #def create_playlists(self, spot_user, spot_pass):
    #    spotifydogvibes.login(spot_user, spot_pass)
    #    pl = spotifydogvibes.get_playlists()
    #
    #    for l in pl:
    #        print l
    #        songs = spotifydogvibes.get_songs(l["index"])
    #        print "found " + str(len(songs)) + " songs in playlist " + str(l["index"])
    #        # -- spam --
    #        #for s in songs:
    #            #print s
    #
    #    spotifydogvibes.logout()


    def get_src(self):
        if self.created == False:
            self.bin = gst.Bin(self.name)
            print "Logging on to spotify"
            self.spotify = gst.element_factory_make("spot", "spot")
            self.spotify.set_property ("user", self.user);
            self.spotify.set_property ("pass", self.passw);
            self.spotify.set_property ("buffer-time", 10000000);
            self.bin.add(self.spotify)
            gpad = gst.GhostPad("src", self.spotify.get_static_pad("src"))
            self.bin.add_pad(gpad)
            self.created = True
        return self.bin

    def search (self, query):
        tracks = []

        url = "http://ws.spotify.com/search/1/track?q=" + query
        tree = ET.parse(urllib.urlopen(url))

        ns = "http://www.spotify.com/ns/music/1"

        for e in tree.findall('.//{%s}track' % ns):
            track = {}
            track['title'] = e.find('.//{%s}name' % ns).text
            track['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            track['album'] = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text)) * 1000
            track['uri'] = e.items()[0][1]
            tracks.append(track)

        return tracks

    def list(self, type):
        return[]

    def set_track (self, track):
        self.spotify.set_property ("spotifyuri", track.uri)
