import os
import re
import urllib
import hashlib
import StringIO
import logging
from PIL import Image

art_dir = 'albumart'

# TODO: perhaps an AlbumArt factory should be inited on startup instead of
# using classmethods?

uncached = []

class AlbumArt():
    @classmethod
    def get_image(self, artist, album, size = 0):
        size = int(size)
        if not os.path.exists(art_dir):
            os.mkdir(art_dir)

        # Need this for Swedish and other peculiar languages to pass
        artist = artist.encode('utf-8')
        album = album.encode('utf-8')

        img_hash = hashlib.sha224(artist + album).hexdigest()
        img_path = art_dir + '/' + img_hash + '.jpg'

        if img_path in uncached:
            #print "uncached cover for %s - %s" % (artist, album)
            img_data = self.get_standard_image()
        elif os.path.exists(img_path):
            #print "using existing cover for %s - %s" % (artist, album)
            # open a previously cached cover
            f = open(img_path, 'rb')
            img_data = f.read()
            f.close()
        else:
            img_data = self.get_image_data(artist, album)
            if img_data == None:
                # open standard cover
                img_data =  self.get_standard_image()
                #print "standard cover for %s - %s" % (artist, album)
                uncached.append(img_path)
            else:
                # save cover to cache
                f = open(img_path, 'wb')
                f.write(img_data)
                f.close()

        # Resize upon request. Nothing special about 640. Just need a limit...
#        if size > 0 and size < 640:
#            buf = StringIO.StringIO(img_data)
#            try:
#                img = Image.open(buf)
#            except:
#                logging.warning("Could not read image: %s" % img_path)
#                return None
#
#            # Won't grow the image since I couldn't get .resize() to work
#            img.thumbnail((size, size), Image.ANTIALIAS)
#
#            # Need to create new buffer, otherwise changes won't take effect
#            out_buf = StringIO.StringIO()
#            img.save(out_buf, 'PNG')
#            out_buf.seek(0)
#            img_data = out_buf.getvalue()
#            buf.close()

        return img_data

    @classmethod
    def get_standard_image(self, size = 0):
        f = open(art_dir + '/default.png', 'rb')
        img_data = f.read()
        f.close()
        return img_data

    @classmethod
    def get_image_data(self, artist, album):
        url_template = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%s&artist=%s&album=%s"
        api_key = "791d5539710d7aa73df0273149ac8761"
        secret_key = "71c595cf3ebae6ccfaebc364c65646a0" # kept for later
        artist = re.sub(' ', '+', artist)
        album = re.sub(' ', '+', album)

        url = url_template % (api_key, artist, album)
        fd = urllib.urlopen(url)
        xml = fd.read()

        sizes = re.findall('<image size="(small|medium|large|extralarge)">(.*)</image>', xml)
        if sizes == []:
            return None

        # last item is extralarge, then large etc
        art_uri = sizes[-1][1]
        try:
            return urllib.urlopen(art_uri).read()
        except IOError:
            logging.debug("Could not open album art URI for %s - %s" % (artist, album))
            return None

if __name__ == '__main__':
    img_data = AlbumArt.get_image('oasis', 'stop the clocks', 80)
    im = cStringIO.StringIO(img_data)
    img = Image.open(im)
    img.save('image.jpg')
