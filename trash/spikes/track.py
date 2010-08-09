class Track:
    name = "Name";
    artist = "Artist"
    def __str__(self):
        return self.artist + ' - ' + self.name
    def to_dict(self):
        return dict(name = self.name, artist = self.artist)

### "main" ###

t = Track()
t.name = "Marathon"
t.artist = "Head Unit"

print t # The override on __str__ makes this work
print t.to_dict() # To be used in D-Bus returns
