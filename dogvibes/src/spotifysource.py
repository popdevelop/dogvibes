import gst
import urlparse, urllib
import xml.etree.ElementTree as ET
from models import Track
import threading

class SpotifySource:

    def __init__(self, name, user, passw):
        self.name = name
        self.passw = passw
        self.user = user
        self.created = False
        self.amp = None
        self.search_prefix = "spotify"
        self.spotify = None
        self.bin = None
        self.tracks = []
        self.condition = threading.Condition()
        self.lock = threading.Lock()

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['spotify']
        del odict['bin']
        del odict['amp']
        del odict['condition']
        del odict['lock']
        del odict['tracks']
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)   # update attributes
        self.created = False
        self.amp = None
        self.condition = threading.Condition()
        self.lock = threading.Lock()
        self.tracks = []
        self.get_src()

    @classmethod
    def strip_protocol(self, uri):
        uri = uri.split("://")
        if len(uri) != 2:
            return None
        return uri[1]

    def create_track_from_uri(self, uri):
        uri = SpotifySource.strip_protocol(uri)
        if uri == None:
            return None
        url = "http://ws.spotify.com/lookup/1/?uri=" + uri

        try:
            e = ET.parse(urllib.urlopen(url))
        except Exception as e:
            return None

        ns = "http://www.spotify.com/ns/music/1"

        if 'album' in uri:
            title = ""
            artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album = e.find('.//{%s}name' % ns).text
            duration = 0
            album_uri = uri
        else:
            title = e.find('.//{%s}name' % ns).text
            artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
            duration = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            album_uri = "spotify://" + e.find('.//{%s}album' % ns).attrib['href']

        track, created = Track.objects.get_or_create(uri="spotify://" + uri,
                                                     defaults={'artist': artist, 'title': title, 'album': album,
                                                               'album_uri': "spotify://" + album_uri, 'duration': duration})
        return track

    def create_tracks_from_uri(self, uri):
        if uri == None:
            return None
        if uri[18:23] == "album":
            album = self.get_album(uri)
            return self.create_tracks_from_album(album)
        else:
            tracks = []
            uri = SpotifySource.strip_protocol(uri)
            if uri == None:
                return None
            url = "http://ws.spotify.com/lookup/1/?uri=" + uri

            try:
                e = ET.parse(urllib.urlopen(url))
            except Exception as e:
                return None

            ns = "http://www.spotify.com/ns/music/1"

            if 'album' in uri:
                title = ""
                artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
                album = e.find('.//{%s}name' % ns).text
                duration = 0
                album_uri = uri
            else:
                title = e.find('.//{%s}name' % ns).text
                artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
                album = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
                duration = int(float(e.find('.//{%s}length' % ns).text) * 1000)
                album_uri = "spotify://" + e.find('.//{%s}album' % ns).attrib['href']

            track, created = Track.objects.get_or_create(uri="spotify://" + uri,
                                                         defaults={'artist': artist, 'title': title, 'album': album,
                                                                   'album_uri': "spotify://" + album_uri, 'duration': duration})
            tracks.append(track)
            return tracks

    def create_tracks_from_album(self, album):
        tracks = []
        for track in album['tracks']:
            title = track['title']
            artist = track['artist']
            album = album['name']
            album_uri = album['uri']
            duration = track['duration']
            tmptrack = Track(uri, title=title, artist=artist, album=album,
                             album_uri=album_uri, duration=duration)
            tracks.append(tmptrack)
        return tracks

    def create_playlists(self, spot_user, spot_pass):
        pass

    def relogin(self, user, passw):
        self.user = user
        self.passw = passw
        if self.created == False:
            self.get_src()
        else:
            self.spotify.set_property ("logged-in", False);
            self.spotify.set_property ("user", self.user);
            self.spotify.set_property ("pass", self.passw);
            self.spotify.set_property ("logged-in", True);

    def get_src(self):
        if self.created == False:
            self.bin = gst.Bin(self.name)
            self.spotify = gst.element_factory_make("spot", "source")
            self.spotify.set_property ("user", self.user);
            self.spotify.set_property ("pass", self.passw);
            self.spotify.set_property ("spotifykeyfile", "dogspotkey.key");
            self.spotify.set_property ("logged-in", True);
            self.spotify.set_property ("buffer-time", 10000000);
            self.bin.add(self.spotify)
            gpad = gst.GhostPad("src", self.spotify.get_static_pad("src"))
            self.bin.add_pad(gpad)
            self.created = True
            # Connect playtoken lost signal
            self.spotify.connect('play-token-lost', self.play_token_lost)
            self.spotify.connect('search-finished', self.search_finished)
        return self.bin

    def search_finished(self, src, result):
        result = eval(result)

        for track in result['tracks']:
            track['artist'] = track['artist'].encode('raw_unicode_escape').decode('utf-8')
            track['title'] = track['title'].encode('raw_unicode_escape').decode('utf-8')
            track['album'] = track['album'].encode('raw_unicode_escape').decode('utf-8')
        self.tracks = result['tracks'] 

        self.condition.acquire()
        self.condition.notify()
        self.condition.release()

    def search(self, query):
        self.condition.acquire()
        self.spotify.set_property("search", query.encode('utf-8'))
        self.condition.wait()
        self.condition.release()
        return self.tracks


    def get_albums(self, query):
        #artist_uri = SpotifySource.strip_protocol(artist_uri)

        ns = "http://www.spotify.com/ns/music/1"

        query = urllib.quote(urllib.unquote(query).encode('utf8'),'=&?/')
        url = u"http://ws.spotify.com/search/1/artist?q=%s" % query

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return []

        artist_uri = tree.find('.//{%s}artist' % ns)
        if artist_uri == None:
            print "ERROR: Empty fetch from %s" % url
            return []

        artist_uri = artist_uri.attrib['href']

        url = u"http://ws.spotify.com/lookup/1/?uri=%s&extras=albumdetail" % artist_uri

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return []

        albums = []

        for e in tree.findall('.//{%s}album' % ns):
            album = {}
            album['uri'] = 'spotify://' + e.attrib['href']
            album['name'] = e.find('.//{%s}name' % ns).text
            album['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album['released'] = e.find('.//{%s}released' % ns).text
            territories = e.find('.//{%s}availability/{%s}territories' % (ns, ns)).text
            if territories != None and ('SE' in territories or territories == 'worldwide'):
                albums.append(album)

        return albums

    def get_album(self, album_uri):
        album_uri = SpotifySource.strip_protocol(album_uri)

        url = "http://ws.spotify.com/lookup/1/?uri=%s&extras=trackdetail" % album_uri

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return None

        ns = "http://www.spotify.com/ns/music/1"

        album = {}
        tracks = []

        album['uri'] = album_uri
        album['name'] = tree.find('.//{%s}name' % ns).text
        album['artist'] = tree.find('.//{%s}artist//{%s}name' % (ns, ns)).text
        album['released'] = tree.find('.//{%s}released' % ns).text

        territories = tree.find('.//{%s}availability/{%s}territories' % (ns, ns)).text
        if 'SE' not in territories and territories != 'worldwide':
            return None

        for e in tree.findall('.//{%s}track' % ns):
            track = {}
            track['title'] = e.find('.//{%s}name' % ns).text
            track['track_number'] = e.find('.//{%s}track-number' % ns).text
            track['disc_number'] = e.find('.//{%s}disc-number' % ns).text
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            track['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            track['uri'] = "spotify://" + e.items()[0][1]
            track['popularity'] = e.find('.//{%s}popularity' % ns).text
            tracks.append(track)

        album['tracks'] = tracks
        return album

    def list(self, type):
        return[]

    def set_track(self, track):
        self.spotify.set_property ("uri", track.uri)

    def uri_matches(self, uri):
        return (uri[0:10] == "spotify://")

    def play_token_lost(self, data):
        # Pause connected amp if play_token_lost is recieved
        if self.amp != None:
            self.amp.API_pause(None)

if __name__ == '__main__':
    src = SpotifySource(None, None, None)
    t =  src.create_track_from_uri("http://spotify:track:3uqinR4FCjLv28bkrTdNX5")
#    print src.get_album("spotify://spotify:album:6G9fHYDCoyEErUkHrFYfs4")
