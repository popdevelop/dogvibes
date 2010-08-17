import os
import re
import urllib
import hashlib
import StringIO
import logging
from PIL import Image
from tornado import httpclient
from time import time

art_dir = 'albumart'
available_sizes = [320, 150, 48]

class AlbumArt():

    # shared by all instances
    uncached = []

    def __init__(self, callback):
        self.http_client = httpclient.AsyncHTTPClient()
        self.callback = callback

    def fetch(self, artist, album, size):
        self.artist = artist.encode('utf-8')
        self.album = album.encode('utf-8')
        self.size = size

#        for s in available_sizes:
#            if size >= s:
#                self.size = s:
#                break

        size = int(size)
        if not os.path.exists(art_dir):
            os.mkdir(art_dir)

        img_hash = hashlib.sha224(self.artist + self.album).hexdigest()
        img_path = art_dir + '/' + img_hash + '.jpg'
        self.img_path = img_path

        if img_path in self.uncached:
            self.callback(self.get_standard_image())
            return
        elif os.path.exists(img_path):
            # FIXME: blocking!
            f = open(img_path, 'rb')
            img_data = f.read()
            f.close()
            self.callback(img_data)
            return
        else:
            self.get_image_data(self.artist, self.album)

    def get_standard_image(self, size = 0):
        f = open(art_dir + '/default.png', 'rb')
        img_data = f.read()
        f.close()
        return img_data

    def get_image_data(self, artist, album):
        url_template = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%s&artist=%s&album=%s"
        api_key = "791d5539710d7aa73df0273149ac8761"
        secret_key = "71c595cf3ebae6ccfaebc364c65646a0" # kept for later
        artist = re.sub(' ', '+', artist)
        album = re.sub(' ', '+', album)

        url = url_template % (api_key, artist, album)
        fd = urllib.urlopen(url)
        self.http_client.fetch(url, self.xml_callback)

    def xml_callback(self, response):
        if (response.body == None):
            self.uncached.append(self.img_path)
            self.callback(self.get_standard_image())
            return

        xml = response.body

        sizes = re.findall('<image size="(small|medium|large|extralarge)">(.*)</image>', xml)
        if sizes == []:
            self.uncached.append(self.img_path)
            self.callback(self.get_standard_image())
            return

        # last item is extralarge, then large etc

        art_uri = sizes[-1][1]
        if art_uri == '':
            self.uncached.append(self.img_path)
            self.callback(self.get_standard_image())
            return

        self.http_client.fetch(art_uri, self.image_callback)

    def image_callback(self, response):
        if (response.body == None):
            self.callback(self.get_standard_image(self.size))
        else:
        # Resize upon request. Nothing special about 640. Just need a limit...
            img_data = response.body
            buf = StringIO.StringIO(img_data)
            try:
                img = Image.open(buf)
            except:
                logging.warning("Could not read image: %s" % self.img_path)
                self.callback(self.get_standard_image())
                return None

            # Won't grow the image since I couldn't get .resize() to work
            size = 150
            img.thumbnail((size, size), Image.ANTIALIAS)

            # Need to create new buffer, otherwise changes won't take effect
            out_buf = StringIO.StringIO()
            img.save(out_buf, 'PNG')
            out_buf.seek(0)
            img_data = out_buf.getvalue()
            buf.close()

            f = open(self.img_path, 'wb')
#            f.write(response.body)
            f.write(img_data)
            f.close()
            self.callback(img_data)
