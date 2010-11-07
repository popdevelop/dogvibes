import unittest
import optparse
import simplejson
import time
import urllib

#change the following setup for testing
#*********************************
#dogvibes user
user = "gyllen"
#*********************************

#valid track information
valid_uris = [{'album': 'Stop The Clocks', 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2CT3r93YuSHtm57mjxvjhH', 'album_uri': 'spotify://spotify:album:1f4I0SpE0O8yg4Eg2ywwv1', 'duration': 258613, 'id': '1'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7H0jlAh4VoUtdeBUurXae9', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 287827, 'id': '2'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Wonderwall (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:18VX67SULc7JttH3OCJhoe', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 252600, 'id': '3'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7DyaMtpjSalQDyfBhetmeb', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 327600, 'id': '4'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5bj4hb0QYTs44PDiwbI5CS', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 258906, 'id': '5'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Stop Crying Your Heart Out', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:3Od1CcijhWjHvrWubZcTKy', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 303133, 'id': '6'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2o9F2fDAzOukxPJd3E7KPg', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 450373, 'id': '7'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': 'Stand By Me', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0C0N5NC7eLj0bjuvyoxV0v', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 356627, 'id': '8'}, {'album': 'Oasis', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Soundscapes - Relaxing Music', 'uri': 'spotify://spotify:track:2OBKFZCMYmA2uMfDYNBIds', 'album_uri': 'spotify://spotify:album:2Cthj8vgO3jfxf8jPTm4nI', 'duration': 389227, 'id': '9'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Live Forever', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:6etTGUYDxGHcqHYI4xBr1w', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 276867, 'id': '10'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Some Might Say', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2j4l3NjUbc7Rn5QyiOPHEf', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 328533, 'id': '11'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Morning Glory', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:1JbZfGJvTwB8gL2lvNwy74', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 303533, 'id': '12'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:23jVJY4xZEBCJjbqjjxZ3q', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 392067, 'id': '13'}, {'album': "Bella's Lullaby: Sentimental Piano Music", 'votes': '0', 'voters': [], 'title': 'Relaxing Oasis', 'artist': 'Michael Silverman', 'uri': 'spotify://spotify:track:673LSyfLrz6fyYsOYDPmNY', 'album_uri': 'spotify://spotify:album:3OeNb61nRXUnMyoTDI2aRG', 'duration': 141307, 'id': '14'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Little By Little', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2eRaVQyrYYVDoreahhjdeu', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 292867, 'id': '15'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:2C9dkOD7JndaNenSihfHjG', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 300680, 'id': '16'}, {'album': 'Wibbling Rivalry', 'votes': '0', 'voters': [], 'title': "Noel's Track", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5MR2GAKVGpd6BS1HUIBesn', 'album_uri': 'spotify://spotify:album:7grONM99Dy9bjNFpOGdg10', 'duration': 425343, 'id': '17'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Supersonic', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0t2TNeixujbaKqEeMSXaLu', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 283707, 'id': '18'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Stand By Me (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:0BJYM0K7daKdA4orsSA5bB', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 287747, 'id': '19'}, {'album': 'Who Killed Amanda Palmer', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Amanda Palmer', 'uri': 'spotify://spotify:track:2hbyKayBajgNfANABSVwYy', 'album_uri': 'spotify://spotify:album:55MoQXHYxkNlD5lxZOjoeG', 'duration': 126933, 'id': '20'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "She's Electric", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2P17rrqMxe014BjoUjsjpL', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 220533, 'id': '21'}, {'album': 'The Masterplan', 'votes': '0', 'voters': [], 'title': 'The Masterplan', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2U251IRExvlUvri5awaJEz', 'album_uri': 'spotify://spotify:album:44CgYD439MapEZryBlTJxD', 'duration': 322507, 'id': '22'}, {'album': 'Essential Bands', 'votes': '0', 'voters': [], 'title': 'The Importance Of Being Idle', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5wo4UpIU17W5knrznFyYqu', 'album_uri': 'spotify://spotify:album:2ravCeM1o3ZoDZkMbRA2Df', 'duration': 221200, 'id': '23'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': "Don't Go Away", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2ERjXtXdYW2ezoJSFSKZwp', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 288640, 'id': '24'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Live Forever (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:5LRw05NYgex2DPuK79Q8tH', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 272080, 'id': '25'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Cast No Shadow', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5zwyQT5gJ0VX5zJoFMDLt7', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 291600, 'id': '26'}]

def dcall(call):
    call = "http://dogvib.es/%s" % (user, call)

    print "calling: %s" % call

    ret = simplejson.load(urllib.urlopen(call))
    if ret['error'] != 0:
        raise Exception()

    # return result if there is one
    try:
        r = ret['result']
        return r
    except:
        return None

class testTheDog(unittest.TestCase):
    def setUp(self):
        dcall("stop")
        dcall("cleandatabase")

class testUserHandling(testTheDog):
    def setUp(self):
        pass

    def test_list(self):
        pass

class testPlaylist(testTheDog):
    def setUp(self):
        pass

    def test_addingremoving(self):
        pass

    def test_skipping(self):
        pass

class testVoting(testTheDog):
    def setUp(self):
        pass

    def test_vote_count(self):
        pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = optparse.OptionParser()
    parser.add_option('-m', '--module', help='Module to run', dest='module', default=None)
    (options, args) = parser.parse_args()

    # Find all tests
    for k, v in globals().items():
        if inspect.isclass(v):
            if  options.module == None or k == options.module:
                suite = unittest.TestLoader().loadTestsFromTestCase(v)
                unittest.TextTestRunner(verbosity=2).run(suite)
