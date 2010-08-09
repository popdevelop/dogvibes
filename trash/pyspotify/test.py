#!/usr/bin/env python
import spotifydogvibes

spotifydogvibes.login("gyllen", "bobidob20")
print spotifydogvibes.search("album:Dylan")
print spotifydogvibes.create_track_from_uri("spotify:track:3oRlTDgnXUrKLaz7mRHLOl")
