from track import Track
from collection import Collection
import config

class FileSource:
    amp = None

    def __init__(self, name, directory):
        self.name = name
        self.directory = directory

        # create database of files
        self.collection = Collection()
        self.collection.index(directory)

    def create_track_from_uri(self, uri):
        return self.collection.create_track_from_uri(uri)

    def create_tracks_from_uri(self, uri):
        return self.collection.create_tracks_from_uri(uri)

    def search(self, query):
        return self.collection.search(query)

    def get_albums(self, query):
        return []

    def get_album(self, album_uri):
        return None

    def list(self, type):
        return self.collection.list(type)

    def uri_matches(self, uri):
        return False

