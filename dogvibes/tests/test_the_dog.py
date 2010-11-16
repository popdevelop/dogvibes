import unittest
import optparse
import simplejson
import time
import urllib
import signal
import inspect

#change the following setup for testing
#*********************************
#dogvibes user
user = "gyllen"
debug = False
#*********************************

#valid track information
valid_uris = [{'album': 'Stop The Clocks', 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2CT3r93YuSHtm57mjxvjhH', 'album_uri': 'spotify://spotify:album:1f4I0SpE0O8yg4Eg2ywwv1', 'duration': 258613, 'id': '1'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7H0jlAh4VoUtdeBUurXae9', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 287827, 'id': '2'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Wonderwall (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:18VX67SULc7JttH3OCJhoe', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 252600, 'id': '3'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7DyaMtpjSalQDyfBhetmeb', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 327600, 'id': '4'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5bj4hb0QYTs44PDiwbI5CS', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 258906, 'id': '5'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Stop Crying Your Heart Out', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:3Od1CcijhWjHvrWubZcTKy', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 303133, 'id': '6'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2o9F2fDAzOukxPJd3E7KPg', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 450373, 'id': '7'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': 'Stand By Me', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0C0N5NC7eLj0bjuvyoxV0v', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 356627, 'id': '8'}, {'album': 'Oasis', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Soundscapes - Relaxing Music', 'uri': 'spotify://spotify:track:2OBKFZCMYmA2uMfDYNBIds', 'album_uri': 'spotify://spotify:album:2Cthj8vgO3jfxf8jPTm4nI', 'duration': 389227, 'id': '9'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Live Forever', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:6etTGUYDxGHcqHYI4xBr1w', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 276867, 'id': '10'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Some Might Say', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2j4l3NjUbc7Rn5QyiOPHEf', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 328533, 'id': '11'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Morning Glory', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:1JbZfGJvTwB8gL2lvNwy74', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 303533, 'id': '12'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:23jVJY4xZEBCJjbqjjxZ3q', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 392067, 'id': '13'}, {'album': "Bella's Lullaby: Sentimental Piano Music", 'votes': '0', 'voters': [], 'title': 'Relaxing Oasis', 'artist': 'Michael Silverman', 'uri': 'spotify://spotify:track:673LSyfLrz6fyYsOYDPmNY', 'album_uri': 'spotify://spotify:album:3OeNb61nRXUnMyoTDI2aRG', 'duration': 141307, 'id': '14'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Little By Little', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2eRaVQyrYYVDoreahhjdeu', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 292867, 'id': '15'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:2C9dkOD7JndaNenSihfHjG', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 300680, 'id': '16'}, {'album': 'Wibbling Rivalry', 'votes': '0', 'voters': [], 'title': "Noel's Track", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5MR2GAKVGpd6BS1HUIBesn', 'album_uri': 'spotify://spotify:album:7grONM99Dy9bjNFpOGdg10', 'duration': 425343, 'id': '17'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Supersonic', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0t2TNeixujbaKqEeMSXaLu', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 283707, 'id': '18'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Stand By Me (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:0BJYM0K7daKdA4orsSA5bB', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 287747, 'id': '19'}, {'album': 'Who Killed Amanda Palmer', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Amanda Palmer', 'uri': 'spotify://spotify:track:2hbyKayBajgNfANABSVwYy', 'album_uri': 'spotify://spotify:album:55MoQXHYxkNlD5lxZOjoeG', 'duration': 126933, 'id': '20'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "She's Electric", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2P17rrqMxe014BjoUjsjpL', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 220533, 'id': '21'}, {'album': 'The Masterplan', 'votes': '0', 'voters': [], 'title': 'The Masterplan', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2U251IRExvlUvri5awaJEz', 'album_uri': 'spotify://spotify:album:44CgYD439MapEZryBlTJxD', 'duration': 322507, 'id': '22'}, {'album': 'Essential Bands', 'votes': '0', 'voters': [], 'title': 'The Importance Of Being Idle', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5wo4UpIU17W5knrznFyYqu', 'album_uri': 'spotify://spotify:album:2ravCeM1o3ZoDZkMbRA2Df', 'duration': 221200, 'id': '23'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': "Don't Go Away", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2ERjXtXdYW2ezoJSFSKZwp', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 288640, 'id': '24'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Live Forever (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:5LRw05NYgex2DPuK79Q8tH', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 272080, 'id': '25'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Cast No Shadow', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5zwyQT5gJ0VX5zJoFMDLt7', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 291600, 'id': '26'}]

#helper functions
#*********************************
def dbg(str):
    if debug:
        print str

def add_all_tracks_to_playlist(playlist):
    for v in valid_uris:
        dcall("playlist/%s/add?uri=%s" % (playlist, v['uri']))

def vote_all_tracks_to_playlist(playlist):
    for v in valid_uris:
        dcall("playlist/%s/vote?uri=%s" % (playlist, v['uri']))

def unvote_all_tracks_in_playlist(playlist):
    for v in valid_uris:
        dcall("playlist/%s/unvote?uri=%s" % (playlist, v['uri']))

def vote_some_tracks_to_playlist(playlist, nbr):
    i = 0
    for v in valid_uris:
        dcall("playlist/%s/vote?uri=%s" % (playlist, v['uri']))
        i = i + 1
        if i >= nbr:
            return


def dcall(call):
    return dcall_full(call, False)

def dcall_full(call, expect_exception):
    call = "http://dogvib.es/%s/%s" % (user, call)

    dbg("-------------------------------")
    dbg("calling: %s" % call)

    ret = urllib.urlopen(call)
    ret = simplejson.load(ret)
    if ret['error'] != 0 and not expect_exception:
        raise Exception()
    elif ret['error'] != 0 and expect_exception:
        return True
    elif ret['error'] == 0 and expect_exception:
        return False

    # return result if there is one
    try:
        r = ret['result']
        dbg("got result: %s" % r)
        return r
    except:
        dbg("returns no result")
        return None
#*********************************

#Tests
#*********************************
class testTheDog(unittest.TestCase):
    def setUp(self):
        dcall("cleandatabase")
        dcall("stop")

class testPlaylist(testTheDog):
    pnames = None

    def setUp(self):
        dcall("cleandatabase")
        self.pnames = ["test1", "test2", "test3", "test4", "test5"]

        dbg("adding test playlists")
        for pn in self.pnames:
            dcall("addplaylist?name=%s" % pn)

    def test_adding_strange_names(self):
        snames = ["test", "test1", "test 2", "testlal"]

        dbg("adding playlists with with test names")
        for sn in snames:
            dcall("addplaylist?name=%s" % sn)

    def test_listing(self):
        plists = dcall("playlists")

        dbg("check listing of playlists work")
        for i,p in enumerate(plists):
            print self.pnames[i]
            print p['name']
            self.assertTrue(p['name'] == self.pnames[i])

class testPlaylist2(testTheDog):
    pname = None

    def setUp(self):
        dcall("cleandatabase")
        self.pnames = ["test1", "test2", "test3", "test4", "test5"]

        dbg("adding test playlists")
        for pn in self.pnames:
            dcall("addplaylist?name=%s" % pn)

    def test_settoactive(self):
        dbg("Test setting none existing playlist to active")
        self.assertTrue(dcall_full("playlist/300/setactive", True))

        plists = dcall("playlists")

        for p in plists:
            dcall("playlist/%d/setactive" % p['id'])
            st = dcall("status")
            self.assertTrue(st['playlist_id'] == p['id'])

    def test_removing(self):
        plists = dcall("playlists")
        dbg("Test removing active list (should not be allowed to")
        dcall_full("playlist/%d/remove" % plists[0]['id'], True);
        dcall("playlist/%d/remove" % plists[1]['id']);
        dcall("playlist/%d/remove" % plists[2]['id']);

class testSearching(testTheDog):
    def test_search(self):
        dcall("search?q='bob dylan'")
        dcall("search?q='oasis'")

class testVolume(testTheDog):
    def test_volume(self):
        dcall("volume?level=0.1")

class testPlayedMilliSeconds(testTheDog):
    def test_playedmilliseconds(self):
        dcall("playedmilliseconds")

#class testUserHandling(testTheDog):
#    def setUp(self):
#        pass
#
#    def test_list(self):
#        dcall("users")
#

class testVoting(testTheDog):
    def setUp(self):
        dcall("stop")
        dcall("cleandatabase")
        self.pnames = ["test1", "test2", "test3", "test4", "test5"]

        dbg("adding test playlists")
        for pn in self.pnames:
            dcall("addplaylist?name=%s" % pn)

    def test_easy_vote(self):
        vote_all_tracks_to_playlist(1)

    def test_vote_unvote(self):
        dbg("Test voting by voting all and then unvoting all")
        #tracks = dcall("playlist/1/tracks")
        #for t in tracks:
        #    self.assertTrue(int(t['votes'] == 0))
        vote_all_tracks_to_playlist(1)
        #tracks = dcall("playlist/1/tracks")
        #for t in tracks:
        #    self.assertTrue(int(t['votes'] == 1))
        unvote_all_tracks_in_playlist(1)
        #tracks = dcall("playlist/1/tracks")
        #for t in tracks:
        #    self.assertTrue(int(t['votes'] == 0))

#    def test_vote_count(self):
#        # check integrety
#        res = amp("getUserInfo")
#        self.assertTrue(res['votes'] == 0, "Incorrect vote count")
#
#        # add five more votes
#        for i in range(0,5):
#            amp("addVote?uri=%s" % valid_uris[7]['uri'])
#
#        # remove five wrong votes
#        for i in range(0,5):
#            amp("removeVote?uri=%s" % valid_uris[7]['uri'])
#
#        # check integrety
#        res = amp("getUserInfo")
#        self.assertTrue(res['votes'] == 0, "Incorrect vote count")
#
#        # remove five correct votes
#        for i in range(0,5):
#            amp("removeVote?uri=%s" % valid_uris[i]['uri'])
#
#        # check integrety
#        res = amp("getUserInfo")
#        self.assertTrue(res['votes'] == 5, "not all votes given back correctly")
#
#    def test_voting_positions(self):
#        # add one vote for gyllen
#        amp("addVote?uri=%s&user=gyllen" % valid_uris[0]['uri'])
#        res = amp("getUserInfo?user=gyllen")
#
#        amp("play")
#
#        # check integrity
#        self.assertTrue(res['votes'] == 4, "Incorrect vote count")
#        amp("addVote?uri=%s&user=gyllen" % valid_uris[4]['uri'])
#
#        list = amp("getAllTracksInQueue")
#        self.assertTrue(list[1]['uri'] == valid_uris[4]['uri'], "Inconsistency on moving tracks with voting")
#        res = amp("getUserInfo?user=gyllen")
#        # check integrity
#        print res
#        self.assertTrue(res['votes'] == 3, "Incorrect vote count user has %s votes" % res['votes'])
#        amp("nextTrack")
#        res = amp("getUserInfo?user=gyllen")
#        print res
#        # check integrity
#        self.assertTrue(res['votes'] == 4, "Incorrect vote count user has %s votes" % res['votes'])
#
#        amp("pause")
#
class testVoteRemoveTrack(testTheDog):
    def setUp(self):
        dcall("stop")
        dcall("cleandatabase")
        self.pnames = ["test1"]

        dbg("adding test playlists")
        for pn in self.pnames:
            dcall("addplaylist?name=%s" % pn)

    def test_remove_track(self):
        plist = dcall("playlists")
        plid = plist[0]['id']

        vote_some_tracks_to_playlist(plid, 3)

        info = dcall("info")
        votes = info['votes']
        tracks = dcall("playlist/%d/tracks" % plid)
        dbg("Try removing tracks from playlist")
        dcall("playlist/%d/removetrack?track_id=%d" % (plid, tracks[0]['id']))
        ntracks = dcall("playlist/%d/tracks" % plid)

        dbg("Check that votes has been returned")
        info = dcall("info")
        self.assertTrue(int(votes) == int(info['votes']) - 1)

        dbg("Check that track was removed")
        for n in ntracks:
            self.assertTrue(n['id'] != tracks[0]['id'])

        dbg("Try to remove none existant track")
        dcall_full("playlist/%d/removetrack?track_id=%d" % (plid, tracks[0]['id']), True)

class testSkippingAndJumping(testTheDog):
    plid = -1

    def setUp(self):
        dcall("stop")
        dcall("cleandatabase")
        pname1 = "test1"
        pname2 = "test2"
        pname3 = "test3"

        dbg("add some playlists")
        dcall("addplaylist?name=%s" % pname1)
        dcall("addplaylist?name=%s" % pname2)
        dcall("addplaylist?name=%s" % pname3)

        dbg("get all playlists")
        playlists = dcall("playlists")

        dbg("get first playlists id")
        plid = playlists[0]['id']

        dbg("set %s playlist as active" % pname1)
        dcall("playlist/%s/setactive" % plid)

        dbg("vote on some tracks on playlist")
        vote_all_tracks_to_playlist(plid)


    def test_playingpausingskipping(self):
        test_nbr = 5

        dbg("playing and pausing for a while (%d play and pausing)" % test_nbr)
        for i in range(0,test_nbr):
            dcall("play")
            dcall("pause")

        dbg("Listen for 5 seconds")
        dcall("play")
        time.sleep(5)

        dbg("skipping for a while (%d skips)" % test_nbr)
        dbg("should be safe because some tracks where added")
        for i in range(0,test_nbr):
            dcall("next")

class testStatus(testTheDog):
    def setUp(self):
        pass

    def test_getstatus(self):
        dcall("status")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = optparse.OptionParser()
    parser.add_option('-m', '--module', help='Module to run', dest='module', default=None)
    parser.add_option('-d', '--debug', action="store_true", help='Display debug output', dest='debug', default=False)
    (options, args) = parser.parse_args()
    debug = options.debug

    # Find all tests
    for k, v in globals().items():
        if inspect.isclass(v):
            if  options.module == None or k == options.module:
                suite = unittest.TestLoader().loadTestsFromTestCase(v)
                unittest.TextTestRunner(verbosity=2).run(suite)
