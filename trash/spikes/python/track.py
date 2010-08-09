class Track:
    def __init__(self, uri):
        self.name = "Name"
        self.artist = "Artist"
        self.uri = uri
    def __str__(self):
        return self.artist + ' - ' + self.name
    def to_dict(self):
        return dict(name = self.name, artist = self.artist)

### "main" ###

t = Track("file:///marathon.mp3")
t.name = "Marathon"
t.artist = "Head Unit"

print t # The override on __str__ makes this work
print t.to_dict() # To be used in D-Bus returns
