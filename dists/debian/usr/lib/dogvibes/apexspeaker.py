import gst

class ApexSpeaker:
    def __init__(self, name, ip):
        self.created = False
        self.name = name
        self.ip = ip
        print "Initiated apex speaker"

    def get_speaker(self):
        if self.created == False:
            self.bin = gst.Bin(self.name)
            self.apexsink = gst.element_factory_make("apexsink", "apexsink")
            self.queue2 = gst.element_factory_make("queue2", "queue2")
            self.volume = gst.element_factory_make("volume", "volume")
            self.audioconvert = gst.element_factory_make("audioconvert", "audioconvert")
            self.apexsink.set_property("sync", False)
            self.apexsink.set_property("host", self.ip)
            self.apexsink.set_property("volume", 90)
            self.bin.add(self.queue2)
            self.bin.add(self.volume)
            self.bin.add(self.audioconvert)
            self.bin.add(self.apexsink)
            self.queue2.link(self.volume)
            self.volume.link(self.audioconvert)
            self.audioconvert.link(self.apexsink)
            gpad = gst.GhostPad("sink", self.queue2.get_static_pad("sink"))
            self.bin.add_pad(gpad)
            print "Created apex speaker"
            self.created = True
        return self.bin

    def get_volume(self):
        return self.volume.get_property("volume")

    def set_volume(self, level):
        if (self.volume == None):
            return
        self.volume.set_property("volume", level)
