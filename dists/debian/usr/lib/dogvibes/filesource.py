from track import Track
from collection import Collection
import config

class FileSource:
    def __init__(self, name, directory):
        self.name = name
        self.directory = directory

        # create database of files
        self.collection = Collection()
        self.collection.index(directory)

    def create_track_from_uri(self, uri):
        return self.collection.create_track_from_uri(uri)

    def search(self, query):
        return self.collection.search(query)

    def list(self, type):
        return self.collection.list(type)