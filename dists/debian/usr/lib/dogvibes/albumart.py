import os
import re
import urllib
import hashlib
import cStringIO
from PIL import Image

art_dir = 'albumart'
awsurl = "http://ecs.amazonaws.com/onca/xml"

# TODO: perhaps an AlbumArt factory should be inited on startup instead of
# using classmethods?

class AlbumArt():
    @classmethod
    def get_image(self, artist, album, size = 0):
        if not os.path.exists(art_dir):
            os.mkdir(art_dir)

        img_hash = hashlib.sha224(artist + album).hexdigest()
        img_path = art_dir + '/' + img_hash

        if os.path.exists(img_path):
            # open a previously cached cover
            f = open(img_path, 'rb')
            img_data = f.read()
            f.close()
        else:
            img_data = self.cache_image(artist, album)
            print "standard cover"
            if img_data == None:
                # open standard cover
                return self.get_standard_image()
            else:
                # save cover to cache
                f = open(img_path, 'wb')
                f.write(img_data)
                f.close()

        # Resize upon request. Nothing special about 640. Just need a limit...
        #if size > 0 and size < 640:
        #    im = cStringIO.StringIO(img_data)
        #    img = Image.open(im)
        #    img.resize((size, size), Image.ANTIALIAS)
        #    img_data = img.tostring() # FIXME: How to extract binary data?

        return img_data

    @classmethod
    def get_standard_image(self, size = 0):
        f = open(art_dir + '/dogvibes.jpg', 'rb')
        img_data = f.read()
        f.close()
        return img_data

    @classmethod
    def cache_image(self, artist, album):
        url = self._GetResultURL(self._search(artist, album))
        if not url:
            return None
        img_re = re.compile(r'''registerImage\("original_image", "([^"]+)"''')
        prod_data = urllib.urlopen(url).read()
        m = img_re.search(prod_data)
        if not m:
            return None
        img_url = m.group(1)
        return urllib.urlopen(img_url).read()

    @classmethod
    def _search(self, artist, album):
        data = {
            "Service": "AWSECommerceService",
            "Version": "2005-03-23",
            "Operation": "ItemSearch",
            "ContentType": "text/xml",
            "SubscriptionId": "AKIAIQ74I7SUW5COGZCQ",
            "SearchIndex": "Music",
            "ResponseGroup": "Small",
            }

        data["Artist"] = artist
        data["Keywords"] = album

        fd = urllib.urlopen("%s?%s" % (awsurl, urllib.urlencode(data)))

        return fd.read()

    @classmethod
    def _GetResultURL(self, xmldata):
        url_re = re.compile(r"<DetailPageURL>([^<]+)</DetailPageURL>")
        m = url_re.search(xmldata)
        return m and m.group(1)

if __name__ == '__main__':
    img_data = AlbumArt.get_image('metallica', 'kill em all', 80)
    im = cStringIO.StringIO(img_data)
    img = Image.open(im)
    img.save('image.jpg')
