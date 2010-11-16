import gst
import platform
import logging

class DeviceSpeaker:
    def __init__(self, name):
        self.created = False
        self.name = name
        logging.debug("Initiated device speaker")

    def get_speaker(self):
        if self.created == False:
            self.bin = gst.Bin(self.name)
            if platform.system() == "Linux":
                logging.debug("Server run under GNU/Linux, using alsasink")
                self.devicesink = gst.element_factory_make("alsasink", "alsasink")
            elif platform.system() == "Darwin":
                self.audioconvert = gst.element_factory_make("audioconvert", "audioconvert")
                self.devicesink = gst.element_factory_make("osxaudiosink", "osxaudiosink")
                logging.debug("Server run under Darwin, using audioconvert and osxaudiosink")

            self.queue2 = gst.element_factory_make("queue2", "queue2")
            self.volume = gst.element_factory_make("volume", "volume")
            self.devicesink.set_property("sync", False)
            self.bin.add(self.queue2)
            self.bin.add(self.volume)
            if platform.system() == "Darwin":
                self.bin.add(self.audioconvert)
            self.bin.add(self.devicesink)
            self.queue2.link(self.volume)
            if platform.system() == "Darwin":
                self.volume.link(self.audioconvert)
                self.audioconvert.link(self.devicesink)
            elif platform.system() == "Linux":
                self.volume.link(self.devicesink)
            gpad = gst.GhostPad("sink", self.queue2.get_static_pad("sink"))
            self.bin.add_pad(gpad)
            logging.debug("Created device speaker")
            self.created = True
        return self.bin

    def get_volume(self):
        return self.volume.get_property("volume")

    def set_volume(self, level):
        if (self.volume == None):
            return
        self.volume.set_property("volume", level)
