from twisted.internet.protocol import Protocol, Factory
from twisted.internet import glib2reactor
glib2reactor.install()
from twisted.web import server, resource
from twisted.internet import reactor
import SocketServer
import socket
import logging
import threading
import re
import cjson
from urlparse import urlparse
import sys
from dogvibes import Dogvibes
from threading import Thread
import signal
import optparse
import gobject
import gst
import cgi
import inspect
import urllib
import config
import time

API_VERSION = '0.2'

LOG_LEVELS = {'0': logging.CRITICAL,
              '1': logging.ERROR,
              '2': logging.WARNING,
              '3': logging.INFO,
              '4': logging.DEBUG}

lock = threading.Lock()


def register_dog():
    DEFAULT_EXT_IP = '0.0.0.0'

    int_ip = socket.gethostbyname(socket.gethostname())

    # Try fetching external IP more than once. Sometimes it fails
    for i in range(0,3):
        try:
            response = urllib.urlopen('http://whatismyip.org')
            ext_ip = response.read()
            continue
        except:
            ext_ip = DEFAULT_EXT_IP
            if i < 2:
                time.sleep(1)

    if ext_ip == DEFAULT_EXT_IP:
        print 'Could not get external IP. No connection to Internet?'

    try:
        response = urllib.urlopen('http://dogvibes.com/registerDog?name=%s&password=%s&int_ip=%s&exp_ip=%s&ws_port=%s&http_port=%s&api_version=%s' % (cfg['DOGVIBES_USER'], cfg['DOGVIBES_PASS'], int_ip, ext_ip, cfg['WS_PORT'], cfg['HTTP_PORT'], API_VERSION))
    except:
        print 'Could access dogvibes.com'
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


class AlbumArtServer(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        if request.uri.find('/dogvibes/getAlbumArt') == -1:
            return False

        u = urlparse(request.uri)
        c = u.path.split('/')
        method = 'API_' + c[-1]
        params = cgi.parse_qs(u.query)

        uri = params.get('uri', 'dummy')[0]
        size = int(params.get('size', 0)[0])

        request.setHeader("Content-type", "image/jpeg")
        return dogvibes.API_getAlbumArt(uri, size)


def handle_request(path):

    u = urlparse(path)

    c = u.path.split('/')

    # Hack to avoid utf-8 to be garbled. Under investigation
    us = u.query.split('&')
    query = ""
    for o in us:
        a = o.split('=')
        if a[0] == 'query':
            query = urllib.unquote(a[1].decode('utf8'))

    try:
        callback = None
        data = None
        error = 0
        raw = False

        params = cgi.parse_qs(u.query)
        # use only the first value for each key (feel free to clean up):
        params = dict(zip(params.keys(), map(lambda x: x[0], params.values())))

        if 'callback' in params:
            callback = params.pop('callback')
            if '_' in params:
                params.pop('_')

        if 'msg_id' in params:
            msg_id = params.pop('msg_id')

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

        # Hack to avoid utf-8 to be garbled. Under investigation
        if 'query' in params:
            params['query'] = query

        # call the method
        data = getattr(klass, method).__call__(**params)
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

    if not raw:
        # Add results from method call only if there is any
        if data == None or error != 0:
            data = dict(error = error)
        else:
            data = dict(error = error, result = data)

        data = cjson.encode(data)

        # Wrap result in a Javascript function if a callback is present
        if callback != None:
            data = "%s(%s)" % (callback, data)

    return (data, raw, error)

class HTTPServer(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        (data, raw, error) = handle_request(request.uri)

        if raw:
            request.setHeader("Content-type", "image/png")
        else:
            request.setHeader("Content-type", "application/json")
            #request.setHeader("Content-type", "text/javascript") # no callback

        #self.send_response(400 if error else 200) # Bad request or OK

        return data


server_handshake = '\
HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
WebSocket-Origin: %s\r\n\
WebSocket-Location: %s/\r\n\r\n\
'

clients = []

class WebSocket(Protocol):

    handshaken = False # Indicates if initial setup has been done
    buf = '' # Save unprocessed data between reads

    def connectionMade(self):
        clients.append(self)
        #self.transport.write(server_handshake)

    def connectionLost(self, reason):
        clients.remove(self)
        logging.warning("Disconnected from: ", self.transport.client)

    def handshake(self, data):

        # FIXME: if smaller than header size, we risk missing some initial commands!!

        shake, self.buf = data.split('\r\n\r\n')

        # extract info to send back to client according to the websocket proto
        host = re.findall("Host: ([a-zA-Z0-9\.:/]*)", shake)
        origin = re.findall("Origin: ([a-zA-Z0-9\.:/]*)", shake)

        # re.findall always return an array
        if host == [] or origin == []:
            logging.error("Websocket handshake is wronng, check incoming request ", self.transport.client)
            logging.error(shake)
            self.transport.loseConnection()

        # compile an answer and send back to the client
        new_handshake = server_handshake % (origin[0], "ws://" + host[0])

        self.transport.write(new_handshake)

        self.handshaken = True

    def sendWS(self, data):
        logging.debug("sending to %d: %s" % (self.transport.client[1], data))
        self.transport.write('\x00' + data.encode('utf-8') + '\xff')

    def pushStatus(self):
        # loop through all amps and look for status updates
        amp = dogvibes.amps[0]
        if amp.needs_push_update or dogvibes.needs_push_update:
            data = dict(error = 0, result = amp.API_getStatus())
            data = cjson.encode(data)
            data = 'pushHandler' + '(' + data + ')'

            amp.needs_push_update = False
            dogvibes.needs_push_update = False

            # TODO: maybe use lock from Twisted
            lock.acquire()
            for client in clients:
                client.sendWS(data)
            lock.release()

    def dataReceived(self, data):
        # Handle Flash plugin
        if data.find("<policy-file-request/>") != -1:
            self.transport.write('<?xml version="1.0"?>\n')
            self.transport.write('<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n')
            self.transport.write('<cross-domain-policy>\n')
            self.transport.write('  <allow-access-from domain="*" to-ports="*"/>\n')
            self.transport.write('</cross-domain-policy>')
            self.transport.loseConnection()
            return

        self.buf += data.strip();

        if self.handshaken == False:
            self.handshake(data)

        # FIXME: This won't trigger a push on track change
        self.pushStatus()

        cmds = []

        msgs = self.buf.split('\xff')
        self.buf = msgs.pop()

        for msg in msgs:
            if msg[0] == '\x00':
                cmds.append(msg[1:])

        for cmd in cmds:
            (data, raw, error) = handle_request(cmd)
            self.sendWS(data);

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


    # Load configuration
    cfg = config.load("dogvibes.conf")

    global dogvibes
    dogvibes = Dogvibes()

    factory = Factory()
    factory.protocol = WebSocket
    reactor.listenTCP(int(cfg['WS_PORT']), factory)

    reactor.listenTCP(int(cfg['HTTP_PORT']), server.Site(HTTPServer()))

#    register_dog()

    reactor.run()
