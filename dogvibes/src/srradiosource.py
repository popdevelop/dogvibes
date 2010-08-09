from track import Track
import logging
import xml.etree.ElementTree as ET
import urlparse, urllib
import re

class SRRadioSource:

    def __init__(self, name):
        self.name = name
        self.amp = None
        self.search_prefix = "sr"

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['amp']
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)   # update attributes
        self.amp = None

    def create_track_from_uri(self, uri):
        if 'asx' not in uri:
            return None

        logging.debug("Created track from uri %s in srradiosource", uri)
        u = urllib.urlopen(uri)
        str = re.search('\"mms:.+\"', u.read())

        u = open("sr.xml") 
        tree = ET.parse(u)
        u.close()

        track = Track(str.group(0)[1:-1])

        for e in tree.findall('channel'):
            for k in e.findall('streamingurl'):
                for s in k.findall('url'):
                    if uri in s.text:
                        track.title = e.get('name')

        track.artist = "SR RADIOTRACK"
        track.album = "SR RADIOTRACK"
        track.album_uri = None
        track.duration = 1

        return track     

    def create_tracks_from_uri(self, uri):
        if 'asx' not in uri:
            return None
        else:
            return [self.create_track_from_uri(uri)]

    def get_albums(self, query):
        return []

    def get_album(self, query):
        return None

    def search(self, query):
        tracks = []
        #FIXME: these should be used, and maybe cached or something
        #url = "http://api.sr.se/api/channels/channels.aspx"
        #urllib.urlopen(url)
        u = open("sr.xml") 
        tree = ET.parse(u)
        u.close()

        for e in tree.findall('channel'):
            if query in e.get('name'):
                for k in e.findall('streamingurl'):
                    for s in k.findall('url'):
                        if 'asx' in s.text:
                            if s.get('quality') == "high":
                                #u = urllib.urlopen(s.text)
                                #str = re.search('\"mms:.+\"', u.read())
                                track = {}
                                track['title'] = e.get('name')
                                track['artist'] = "SR RADIOTRACK"
                                track['album'] = "SR RADIOTRACK"
                                track['album_uri'] = None
                                track['duration'] = 1
                                track['uri'] = s.text
                                track['popularity'] = "0"
                                tracks.append(track)
        return tracks

    def uri_matches(self, uri):
        return False

    def list(self, type):
        return[]
