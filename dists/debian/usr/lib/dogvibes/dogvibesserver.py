#!/usr/bin/env python
import os
import inspect
import hashlib
import gobject
import gst

#import dogvibes object
from dogvibes import Dogvibes

# import track
from track import Track
from collection import Collection

# import threads
from threading import Thread

from urlparse import urlparse
import cgi
import json
import sys

import urllib

import signal

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# web server
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import BaseHTTPServer

class ClientHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><body>")
        self.wfile.write("<b>A client should be displayed here. HTML and images is to be fetched from the spotify clone directory</b>")
        self.wfile.write("</html></body>")

class APIHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        c = u.path.split('/')
        method = 'API_' + c[-1]
         # TODO: this should be determined on API function return:
        raw = method == 'API_getAlbumArt'

        obj = c[1]
        id = c[2]
        id = 0 # TODO: remove when more amps are supported

        if obj == 'dogvibes':
            klass = dogvibes
        else:
            klass = dogvibes.amps[id]

        callback = None
        data = None
        error = 0

        params = cgi.parse_qs(u.query)
        # use only the first value for each key (feel free to clean up):
        params = dict(zip(params.keys(), map(lambda x: x[0], params.values())))
        if 'callback' in params:
            callback = params.pop('callback')
            if '_' in params:
                params.pop('_')                

        try:
            # strip params from paramters not in the method definition
            args = inspect.getargspec(getattr(klass, method))[0]
            params = dict(filter(lambda k: k[0] in args, params.items()))        
            # call the method
            data = getattr(klass, method).__call__(**params)
        except AttributeError as e:
            print e
            error = 1 # No such method
        except TypeError as e:
            print e
            error = 2 # Missing parameter
        except DogError as e:
            print e
            error = 3 # Internal error, e.g. could not find specified uri

        self.send_response(400 if error else 200) # Bad request or OK

        if raw:
            self.send_header("Content-type", "image/jpeg")
        else:
            # Add results from method call only if there is any
            if data == None or error != 0:
                data = dict(error = error)
            else:
                data = dict(error = error, result = data)

            # Different JSON syntax in different versions of python
            if sys.version_info[0] >= 2 and sys.version_info[1] >= 6:
                data = json.dumps(data)
            else:
                data = json.write(data)

            # Wrap result in a Javascript function if a callback was submitted
            if callback != None:
                data = callback + '(' + data + ')'
                self.send_header("Content-type", "text/javascript")
            else:
                self.send_header("Content-type", "application/json")

        self.end_headers()
        self.wfile.write(data)

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def serve_client(port):
    server = ThreadingHTTPServer(("", port), ClientHandler)
    server.serve_forever()

class API(Thread):
    def __init__(self):
        Thread.__init__ (self)

    def run(self):
        global dogvibes
        dogvibes = Dogvibes()

        #Thread(target=serve_client, args=[8080]).start()

        server = BaseHTTPServer.HTTPServer(("", 2000), APIHandler)
        server.serve_forever()

def main():
#if __name__ == '__main__':
    #if os.path.exists('dogvibes.db'):
    #    os.remove('dogvibes.db')
    #    print "REMOVING DATABASE! DON'T DO THIS IF YOU WANNA KEEP YOUR PLAYLISTS"

    print "Running Dogvibes."
    print "   ->Vibe the dog!"
    print "                 .--.    "
    print "                / \\aa\_  "
    print "         ,      \_/ ,_Y) "
    print "        ((.------`\"=(    "
    print "         \   \      |o   "
    print "         /)  /__\  /     "
    print "        / \ \_  / /|     "
    print "        \_)\__) \_)_)    "

    # Enable Ctrl-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    gobject.threads_init()

    API().start()

    loop = gobject.MainLoop()
    loop.run()
