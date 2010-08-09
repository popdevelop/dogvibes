#!/usr/bin/env ruby

require "dbus"

# System Bus is for OS events, shared for all users 
bus = DBus::SystemBus.instance
service = bus.service("com.Dogvibes")

########################################
### TESTS FOR THE DOGVIBES INTERFACE ###
########################################

#obj = service.object("/com/dogvibes/dogvibes")
#obj.introspect
#obj.default_iface = "com.Dogvibes.Dogvibes"
#
## TEST: Searching for tracks
#query = "dylan"
#puts "TEST: Searching for #{query}"
#key = nil
#obj.Search(query)[0].each { |song|
#  unless(song.empty?)
#    puts song
#    if key.nil?
#      key = song.split(",")[2]
#    end
#  end
#}

###################################
### TESTS FOR THE AMP INTERFACE ###
###################################

obj = service.object("/com/dogvibes/amp/0")
obj.introspect
obj.default_iface = "com.Dogvibes.Amp"

#todo: obj.ClearQueue()
#todo: obj.disconnectAllSpeakers()

# TEST: Playing the first track
puts "TEST: Queue and print tracks"
#todo: search for these tracks instead
obj.Queue("spotify:track:3A3WCIkkm5MqGRnc4LT6fz")
obj.Queue("spotify:track:3ZlFUr0RBrUYYsmlcFvD0e")
obj.Queue("spotify:track:3q50J3nI1GOjDOwZDjt5Un")
obj.Queue("spotify:track:0S3gpZzlT9Hb7CCSV2owX7")
obj.Queue("spotify:track:69xL3vzKISEij96FrmWYNF")
obj.Queue("spotify:track:3Qvf812dY5JVlaZEbzI3nZ")
obj.Queue("spotify:track:7kXmJwrZGIhDaLT9sNo3ut")
obj.Queue("spotify:track:7rk75X26LwTEE8slwrqMjy")
obj.Queue("spotify:track:5WO8Vzz5hFWBGzJaNI5U5n")
puts obj.GetAllTracksInQueue()
sleep 2

# TEST: Connecting the active speaker
puts "TEST: Playing the track"
obj.Play()
sleep 2

# TEST: Connecting the active speaker
puts "TEST: Connecting the active speaker"
obj.ConnectSpeaker(0)
sleep 2

# TEST: Next track
puts "TEST: Next track"
obj.NextTrack()
sleep 2

# TEST: Next track
puts "TEST: Next track"
obj.NextTrack()
sleep 2

# TEST: Next track
puts "TEST: Previous track"
obj.PreviousTrack()
sleep 2

# TEST: Pausing the track
puts "TEST: Pausing the track"
obj.Pause()
sleep 2

# TEST: Resuming the track
puts "TEST: Resuming the track"
obj.Resume()
sleep 2

# TEST: Skipping to track 5
puts "TEST: Skipping to track 5"
obj.PlayTrack(5)
sleep 2

# TEST: Disconnecting the active speaker
puts "TEST: Disconnecting the active speaker"
obj.DisconnectSpeaker(0)
sleep 2

# TEST: Connecting an other speaker
puts "TEST: Connecting an other speaker"
obj.ConnectSpeaker(1)
sleep 2

# TEST: Connecting the active speaker
puts "TEST: Connecting the active speaker"
obj.ConnectSpeaker(0)
sleep 2

# TEST: Stopping the track
puts "TEST: Stopping the track"
obj.Stop()
sleep 2

# TEST: Playing the track
puts "TEST: Playing the track"
obj.Play()
sleep 2

# TEST: Disconnect the other speaker
puts "TEST: Disconnect the other speaker"
obj.DisconnectSpeaker(1)
sleep 2

# TEST: Stopping the track
puts "TEST: Stopping the track"
obj.Stop()
