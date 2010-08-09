from track import Track
import logging
import gdata.youtube
import gdata.youtube.service
import urlparse, urllib
import re

def PrintVideoFeed(feed):
    for entry in feed.entry:
         PrintEntryDetails(entry)

def PrintEntryDetails(entry):
    print 'Video title: %s' % entry.media.title.text
    print 'Video published on: %s ' % entry.published.text
    print 'Video description: %s' % entry.media.description.text
    print 'Video category: %s' % entry.media.category[0].text
    print 'Video tags: %s' % entry.media.keywords.text
    print 'Video watch page: %s' % entry.media.player.url
    print 'Video flash player URL: %s' % entry.GetSwfUrl()
    print 'Video duration: %s' % entry.media.duration.seconds

    print 'Video view count: %s' % entry.statistics.view_count

    # show alternate formats
    for alternate_format in entry.media.content:
        if 'isDefault' not in alternate_format.extension_attributes:
            print 'Alternate format: %s | url: %s ' % (alternate_format.type,
                                                 alternate_format.url)

    # show thumbnails
    for thumbnail in entry.media.thumbnail:
        print 'Thumbnail url: %s' % thumbnail.url              


class YoutubeSource:

    def __init__(self, name):
        self.name = name
        self.amp = None
        self.search_prefix = "youtube"

    def create_track_from_uri(self, uri):
        if 'youtube' not in uri:
            return None
            
        m = re.search('http://www.youtube.com/get_video.video_id=(.*?)&t=(.*)',uri)

        client = gdata.youtube.service.YouTubeService()
        client.ssl = False

        entry = client.GetYouTubeVideoEntry(video_id=m.group(1))
        logging.debug("Created track from uri %s in youtubesource", uri)
        #PrintEntryDetails(entry)
        swfuri = entry.GetSwfUrl()

        video_id = m.group(1)
        t = m.group(2)

        track = Track(uri)
        track.title = entry.media.title.text
        track.artist = "YOUTUBE VIDEO"
        track.album = entry.media.category[0].text
        #FIXME add search for author on album?
        track.album_uri = None
        track.duration = int(entry.media.duration.seconds)*1000

        return track     

    def create_tracks_from_uri(self, uri):
        if 'youtube' not in uri:
            return None
        else:
            return [self.create_track_from_uri(uri)]

    def get_albums(self, query):
        return []

    def get_album(self, query):
        return None

    def search(self, q):
        client = gdata.youtube.service.YouTubeService()
        client.ssl = False
        
        query = gdata.youtube.service.YouTubeVideoQuery()
        query.vq = q
        query.orderby = 'viewCount'
        #FIXME first 5 and then spotify or interleave?
        query.max_results = '5'

        feed = client.YouTubeQuery(query)

        #instead of flash, use rtsp, these should work
        #for alternate_format in entry.media.content:
        #    if 'isDefault' not in alternate_format.extension_attributes:
        #        print 'Alternate format: %s | url: %s ' % (alternate_format.type,
        #                                             alternate_format.url)

        #FIXME use for albumart?
        #for thumbnail in entry.media.thumbnail:
        #print 'Thumbnail url: %s' % thumbnail.url              

        tracks = []
        for entry in feed.entry:
            track = {}
            track['title'] = entry.media.title.text
            track['artist'] = "YOUTUBE VIDEO"
            track['album'] = entry.media.category[0].text
            track['album_uri'] = None
            track['duration'] = int(entry.media.duration.seconds)*1000

            #FIXME: this is slow!
            swfuri = entry.GetSwfUrl()
            p = re.compile('http://www.youtube.com/v/(.*)\?.*$')
            video_id = p.match(swfuri).group(1)

            uri = "http://www.youtube.com/watch?v="+video_id
            u = urllib.urlopen(uri)
            str = re.search('\"t\": +\"(.+?)\"',u.read())
            t = str.group(1)

            track['uri'] = "http://www.youtube.com/get_video?video_id=" + video_id + "&" + "t=" + t
            track['popularity'] = "0.5"
            tracks.append(track)
        return tracks

    def uri_matches(self, uri):
        return False

    def list(self, type):
        return[]
