#!/usr/bin/env python2.6
import os
import inspect
import hashlib
import gobject
import gst

import threading

from threading import Thread
import socket
import select
import signal
import re
import cgi

#import dogvibes object
from dogvibes import Dogvibes

# import track
from track import Track
from collection import Collection

from urlparse import urlparse
import cjson
import sys

import urllib

import signal

import logging
import optparse

LOG_LEVELS = {'0': logging.CRITICAL,
              '1': logging.ERROR,
              '2': logging.WARNING,
              '3': logging.INFO,
              '4': logging.DEBUG}

lock = threading.Lock()

server_handshake = '\
HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
WebSocket-Origin: %s\r\n\
WebSocket-Location: %s/\r\n\r\n\
'

class Server:
    def __init__(self):
        self.host = ''
        self.port = 9999
        self.nbr_connections = 5
        self.size = 1024
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host,self.port))
            self.server.listen(self.nbr_connections)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        input = [self.server]

        while True:
            # TODO: we could wait for other connections like HTTP on port 80
            inputready,outputready,exceptready = select.select(input,[],[])

            for s in inputready:
                if s == self.server:
                    # handle the server socket
                    c = ClientConnection(self.server.accept(),self)
                    c.start()

        # close all threads

        self.server.close()
#        for c in self.threads:
#            c.join()

    def pushStatus(self):
        # loop through all amps and look for status updates
        amp = dogvibes.amps[0]
        if amp.needs_push_update or dogvibes.needs_push_update:
            data = dict(error = 0, result = amp.API_getStatus())
            data = cjson.encode(data)
            data = 'pushHandler' + '(' + data + ')'

            amp.needs_push_update = False
            dogvibes.needs_push_update = False

            lock.acquire()
            for c in self.threads:
                c.sendWS(data)
            lock.release()



class ClientConnection(threading.Thread):
    def __init__(self,(client,address),parent):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024
        self.data = ''
        self.parent = parent
        self.running = 0

    def handshake(self):
        # FIXME: if smaller than header size, we risk missing some initial commands!!
        shake = self.client.recv(512)

        # extract info to send back to client according to the websocket proto
        host = re.findall("Host: ([a-zA-Z0-9\.:/]*)", shake)
        origin = re.findall("Origin: ([a-zA-Z0-9\.:/]*)", shake)

        # re.findall always return an array
        if host == [] or origin == []:
            print "Websocket handshake is wrong. Check incoming request"
            print shake
            return False

        # compile an answer and send back to the client
        new_handshake = server_handshake % (origin[0], "ws://" + host[0])
        self.client.send(new_handshake)

    def sendWS(self, data):
        try:
            # TODO: make sure data is utf-8
            # TEST: swedish letters
            logging.debug("sending to %d: %s" % (self.address[1], data))
            self.client.send('\x00' + data.encode('utf-8') + '\xff')
        except socket.error as (errno, string):
            if errno == 32:
                # client is not longer present
                logging.debug("Client %s(%s) has disconnected." % (self.address[0], self.address[1]))
                self.running = 0
                return
            else:
                print "ERROR: unknown socket response %s(%d)" % (string, errno)

    def interact(self):
        self.parent.pushStatus()

        try:
            tmp = self.client.recv(256)
        except: return

        self.data += tmp;

        cmds = []

        msgs = self.data.split('\xff')
        self.data = msgs.pop()

        for msg in msgs:
            if msg[0] == '\x00':
                cmds.append(msg[1:])

        for cmd in cmds:
            logging.info("%s(%s): %s" % (self.address[0], self.address[1], cmd))

            # path can be like dogvibes/method or amp/0/method
            u = urlparse(cmd)
            c = u.path.split('/')

            method = 'API_' + c[-1] # last is always method
            obj = c[1] # first is always object
            id = c[2] # TODO: must check len of array for this to work
            id = 0 # TODO: remove when more amps are supported

            if obj == 'dogvibes':
                klass = dogvibes
            else:
                klass = dogvibes.amps[id]

            callback = None
            data = None
            error = 0
            msg_id = None

            params = cgi.parse_qs(u.query)
            # use only the first value for each key (feel free to clean up):
            params = dict(zip(params.keys(), map(lambda x: x[0], params.values())))
            if 'callback' in params:
                callback = params.pop('callback')
                # FIXME: should be allowed to send more parameters
                # than specified. But strip them
                if '_' in params: # TODO: this applies when not using callback as well?
                    params.pop('_')

            if 'callback' in params:
                callback = params.pop('callback')

            if 'msg_id' in params:
                msg_id = params.pop('msg_id')

            try:
                # strip params from paramters not in the method definition
                args = inspect.getargspec(getattr(klass, method))[0]
                params = dict(filter(lambda k: k[0] in args, params.items()))
                # call the method
                data = getattr(klass, method).__call__(**params)
            except AttributeError as e:
                error = 1 # No such method
                logging.info(e)
            except TypeError as e:
                error = 2 # Missing parameter
                logging.info(e)
            except ValueError as e:
                error = 3 # Internal error, e.g. could not find specified uri
                logging.info(e)

            # Add results from method call only if there are any
            if data == None or error != 0:
                data = dict(error = error)
            else:
                data = dict(error = error, result = data)

            # TODO: use '_' instead of 'msg_id'?
            if msg_id != None:
                data['msg_id'] = msg_id

            # Different JSON syntax in different versions of python
            data = cjson.encode(data)

            # Wrap result in a Javascript function if a callback was submitted
            if callback != None:
                #data = callback + '(' + data + ')'
                data = "%s(%s)" % (callback, data)

            self.sendWS(data);


    def run(self):
        self.running = 1
        while self.running:
            if self.handshake() == False:
                self.client.close()
                return
                # FIXME: remove thread

            # Reads can't block since we must always react when other messages
            # arrive from e.g. the amp
            self.client.setblocking(0)

            lock.acquire()
            self.parent.threads.append(self)
            logging.debug(str([a.address[1] for a in self.parent.threads]) + " are now running since latest addition")
            lock.release()

            while self.running:
                # TODO: is this too intense?
                self.interact()

        lock.acquire()
        self.parent.threads.remove(self)
        logging.debug(str([a.address[1] for a in self.parent.threads]) + " are now left in thread pool")
        lock.release()

        logging.debug(str(self.address[1]) + " leaving run()")


class API(Thread):
    def __init__(self):
        Thread.__init__ (self)

    def run(self):
        global dogvibes
        dogvibes = Dogvibes()

        s = Server()
        s.run()


if __name__ == '__main__':

    print "Running Dogvibes (Websocket edition)"
    print "   ->Vibe the dog!"
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
    parser.add_option('-l', help='Log level', dest='log_level', default=3)
    parser.add_option('-f', help='Log file name', dest='log_file', default='/dev/stdout') # TODO: Windows will feel dizzy
    (options, args) = parser.parse_args()
    log_level = LOG_LEVELS.get(options.log_level, logging.NOTSET)
    logging.basicConfig(level=log_level, filename=options.log_file,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    gobject.threads_init()

    API().start()

    loop = gobject.MainLoop()
    loop.run()
