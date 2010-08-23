import os
# Set environmenst variables for making dogvibes run as an OSX app
os.environ['GST_PLUGIN_PATH'] = '../Frameworks'
os.environ['GST_REGISTRY_FORK'] = 'no'
import socket
import logging
import re
import cjson
from urlparse import urlparse
import sys
from dogvibes import Dogvibes
from database import Database
import signal
import optparse
import gobject
import gst
import cgi
import inspect
import urllib
import config
import time
import threading
from tornado import iostream, ioloop

API_VERSION = '0.1'

LOG_LEVELS = {'0': logging.CRITICAL,
              '1': logging.ERROR,
              '2': logging.WARNING,
              '3': logging.INFO,
              '4': logging.DEBUG}

EOS = r'[[EOS]]'
SEP = r'[[SEP]]'
RAW_YES = r'1'
RAW_NO = r'0'
PUSH_YES = r'1'
PUSH_NO = r'0'

def register_dog():
    int_ip = cfg['MASTER_SERVER']
    if int_ip == 'localhost':
        int_ip = socket.gethostbyname(socket.gethostname())

    try:
        response = urllib.urlopen('http://dogvibes.com/registerDog?username=%s&password=%s&host=%s' % (cfg['DOGVIBES_USER'], cfg['DOGVIBES_PASS'], int_ip))
    except:
        print 'Could not access dogvibes.com'
        return

    reply = response.read()
    if reply == '0':
        print 'Registered a client at http://dogvibes.com/%s' % cfg['DOGVIBES_USER']
    elif reply == '1':
        print "Must specify a password to update client '%s'" % cfg['DOGVIBES_USER']
    elif reply == '2':
        print "Password do not match the registered one for client '%s'" % cfg['DOGVIBES_USER']
    else:
        print 'Unknown error when registering client'

def push_status():
    amp = dogvibes.amps[0]
    if amp.needs_push_update or dogvibes.needs_push_update:
        data = amp.get_status()
        amp.needs_push_update = False
        dogvibes.needs_push_update = False
        return_data('0', data, 0, False, 'pushHandler', None, True)

def on_data(command):
    commands = command.split(EOS)[0:-1]
    for c in commands:
        nbr, c, user, avatar_url = c.split(SEP) # remove nbr
        run_command(nbr, c, user, avatar_url)
        push_status()

    stream.read_until(EOS, on_data)

def run_command(nbr, command, user, avatar_url):
    u = urlparse(command)
    c = u.path.split('/')

    # Hack to avoid utf-8 to be garbled. Under investigation
    us = u.query.split('&')
    query = ""
    artist = ""
    album = ""
    for o in us:
        a = o.split('=')
        if a[0] == 'query':
            query = urllib.unquote(a[1].decode('utf8'))
        if a[0] == 'artist':
            artist = urllib.unquote(a[1].decode('utf8'))
        if a[0] == 'album':
            album = urllib.unquote(a[1].decode('utf8'))

    msg_id = None
    js_callback = None
    data = None
    raw = False
    error = 0

    params = cgi.parse_qs(u.query)
    # use only the first value for each key (feel free to clean up):
    params = dict(zip(params.keys(), map(lambda x: x[0], params.values())))

    if 'callback' in params:
        js_callback = params.pop('callback')
    if 'msg_id' in params:
        msg_id = params.pop('msg_id')
    if 'user' in params: # DEBUG: add this to the req to override cookies
        user = params.pop('user')
    if 'avatar_url' in params:
        avatar_url = params.pop('avatar_url')
    if '_' in params:
        params.pop('_')

    request = DogRequest(command, nbr, user, avatar_url, msg_id, js_callback)

    try:
#    if True:
        if (len(c) < 3):
            raise NameError("Malformed command: %s" % u.path)

        method = 'API_' + c[-1]
         # TODO: this should be determined on API function return:
        raw = method == 'API_getAlbumArt'

        obj = c[1]
        #id = c[2]
        id = 0 # TODO: remove when more amps are supported

        if obj == 'dogvibes':
            klass = dogvibes
        elif obj == 'amp':
            klass = dogvibes.amps[id]
        else:
            raise NameError("No such object '%s'" % obj)

        # strip params from paramters not in the method definition
        args = inspect.getargspec(getattr(klass, method))[0]
        params = dict(filter(lambda k: k[0] in args, params.items()))

        for p in params:
            if not isinstance(params[p], str):
                request.finish(error = 5)
                return

        params['request'] = request

        # Hack to avoid utf-8 to be garbled. Under investigation
        if 'query' in params:
            params['query'] = query
        if 'artist' in params:
            params['artist'] = artist
        if 'album' in params:
            params['album'] = album

        getattr(klass, method).__call__(**params)
    except AttributeError as e:
        error = 1 # No such method
        logging.warning(e)
    except TypeError as e:
        error = 2 # Missing parameter
        logging.warning(e)
    except ValueError as e:
        error = 3 # Internal error, e.g. could not find specified uri
        logging.warning(e)
    except NameError as e:
        error = 4 # Wrong object or other URI error
        logging.warning(e)

    if error != 0: # TODO: Don't do it like this! Won't work when threading off
        request.finish(error = error)

    # The request is not ended here, but instead in the DogRequest.callback

class DogRequest:
    def __init__(self, description, nbr, user, avatar_url, msg_id, js_callback):
        self.description = description
        self.nbr = nbr
        self.user = user
        self.avatar_url = avatar_url
        self.msg_id = msg_id
        self.js_callback = js_callback
        self.pushes = []
        self.duration = time.time()

    def push(self, data):
        self.pushes.append(data)

    def finish(self, data = None, error = 0, raw = False, push = False):
        logging.debug("%.3fs: %s" % (time.time() - self.duration, self.description))
        return_data(self.nbr, data, error, raw, self.js_callback, self.msg_id, push)
        joined_pushes = {}
        [ joined_pushes.update(push) for push in self.pushes ]
        if joined_pushes != {}:
            return_data('0', joined_pushes, 0, False, "pushHandler", None, True)

def return_data(nbr, data, error, raw, js_callback, msg_id, broadcast):
    if raw:
        stream.write(nbr + SEP + RAW_YES + SEP + PUSH_NO + SEP + data + EOS)
        return

    res = {}
    if data != None and error == 0:
        res['result'] = data
    if not broadcast:
        res['error'] = error
    if msg_id != None:
        res['msg_id'] = msg_id

    res = cjson.encode(res)

    if js_callback != None:
        res = "%s(%s)" % (js_callback, res)

    if broadcast:
        is_broadcast = PUSH_YES
    else:
        is_broadcast = PUSH_NO

    stream.write(nbr + SEP + RAW_NO + SEP + is_broadcast + SEP + res + EOS)

if __name__ == "__main__":
    print "Running Dogvibes"
    print
    print "  Vibe the dog!"
    print "                 .--.    "
    print "                / \\aa\_  "
    print "         ,      \_/ ,_Y) "
    print "        ((.------`\"=(    "
    print "         \   \      |o   "
    print "         /)  /__\  /     "
    print "        / \ \_  / /|     "
    print "        \_)\__) \_)_)    "
    print "                         "
    print "                         "
    print "   uses SPOTIFY(R) CORE  "
    print "                         "
    print "This product uses SPOTIFY(R) CORE"
    print "but is not endorsed, certified or"
    print "otherwise approved in any way by "
    print "Spotify. Spotify is the registered"
    print "trade mark of the Spotify Group"
    print "                         "

    # Enable Ctrl-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Setup log
    parser = optparse.OptionParser()
    parser.add_option('-l', help='Log level', dest='log_level', default='2')
    parser.add_option('-f', help='Log file name', dest='log_file', default='/dev/stdout') # TODO: Windows will feel dizzy
    (options, args) = parser.parse_args()
    log_level = LOG_LEVELS.get(options.log_level, logging.NOTSET)
    logging.basicConfig(level=log_level, filename=options.log_file,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Setup database tables
    Database()

    # Load configuration
    cfg = config.load("dogvibes.conf")

    global dogvibes
    dogvibes = Dogvibes()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    try:
        s.connect((cfg["MASTER_SERVER"], 8080))
    except socket.error:
        print "Oops! Could not connect to API server at '%s'" % cfg['MASTER_SERVER']
        exit()

    print "Connected to API server at '%s'" % cfg['MASTER_SERVER']

    stream = iostream.IOStream(s)
    stream.write(cfg['DOGVIBES_USER'] + EOS)

    register_dog()

    stream.read_until(EOS, on_data)

    threading.Thread(target=ioloop.IOLoop.instance().start).start()

    gobject.threads_init()
    loop = gobject.MainLoop()
    loop.run()
