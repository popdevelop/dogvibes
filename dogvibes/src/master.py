from tornado import ioloop, iostream, httpserver, web, websocket, database
from tornado.options import define, options
import tornado.options

import errno
import functools
import socket
import albumart_api
import logging
import cgi
import urlparse
import urllib
import os

dogs = {}

LOG_LEVELS = {'0': logging.CRITICAL,
              '1': logging.ERROR,
              '2': logging.WARNING,
              '3': logging.INFO,
              '4': logging.DEBUG}

EOS = r'[[EOS]]'
SEP = r'[[SEP]]'
PUSH_YES = r'1'
PUSH_NO = r'0'
RAW_YES = r'1'
RAW_NO = r'0'

mobile = ["iphone", "ipod", "android", "opera mini", "blackberry", "iris",
          "3g_t", "windows ce", "opera mobi", "windows ce; smartphone;",
          "windows ce; iemobile"]

define("port", default=9990, help="run on the given port", type=int)
define("mysql_host", default="mysql.dogvibes.com", help="blog database host")
define("mysql_database", default="dogvibes", help="blog database name")
define("mysql_user", default="root", help="blog database user")
define("mysql_password", default="pass", help="blog database password")

db = None

class ClientHandler(web.StaticFileHandler):
    def get(self, path, include_body=True):
        # Redirect when not adding slash after username, i.e. dogvib.es/user
        if not self.request.path.endswith("/") and self.request.path.find("/", 1) == -1:
            uri = self.request.path + "/"
            if self.request.query: uri += "?" + self.request.query
            self.redirect(uri)
            return

        if any([i for i in mobile if i in self.request.headers["User-Agent"].lower()]):
            client = "dogbite"
        else:
            client = "dogbone"
        if path == "":
            path = "index.html"
        path = os.path.join(client, path)
        web.StaticFileHandler.get(self, path, include_body)

class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/api/stream/([a-zA-Z0-9]+).*", WSHandler),
            (r"/api/([a-zA-Z0-9]+).*", HTTPHandler),
            (r"/[a-zA-Z0-9]+/?(.*)", ClientHandler,
             {"path": os.path.join(os.path.dirname(__file__), "../../clients")}),
            ]
        web.Application.__init__(self, handlers)
        self.add_transform(ClientGenerator)

class Dog():
    def __init__(self, stream):
        self.stream = stream
        self.active_handlers = []

    def setup(self, data):
        data = data[:-len(EOS)]
        username, password, host = data.split(SEP)
        # TODO: error handling

        db_dog = db.get("SELECT * FROM dogs WHERE username = %s", username)
        if password != db_dog.password:
            logging.info("Wrong password for %s" % username)
            return

        if db_dog is None:
            db.execute("INSERT INTO dogs (username, password, host) VALUES"
                       " (%s, %s, %s)", username, password, host)
        else:
            db.execute("UPDATE dogs SET host = %s WHERE id = %s", host, db_dog.id)

        dog = Dog.find(username)
        if dog != None:
            dog.destroy()
        dogs[username] = self

        logging.info("Welcome, %s!" % username)
        self.username = username
        self.password = password
        self.host = host

    def command_callback(self, data):
        data = data[:-len(EOS)]
        nbr, raw, push, result = data.split(SEP)

        # clean up dangling requests to they are garbage collected
        self.active_handlers = [ h for h in self.active_handlers if h.active() ]

        for handler in self.active_handlers:
            # only return result to the waiting connection
            # however, if this is a push message, all websockets want it
            if handler.nbr == nbr or isinstance(handler, WSHandler) and push == PUSH_YES:
                handler.send_result(raw, result)

        if not self.stream.reading():
            self.stream.read_until(EOS, self.command_callback)

    def send_command(self, command, handler):
        try:
            # FIXME: UnicodeEncodeError: 'ascii' codec can't encode character u'\xf6' in position 46: ordinal not in range(128)
            self.stream.write(handler.nbr + SEP + command + EOS)
        except:
            logging.debug("Failed writing %s to Dog %s" % (command, self.username))
            self.destroy()
            return

        if not self.stream.reading():
            self.stream.read_until(EOS, self.command_callback)

    def destroy(self):
        self.stream.close()
        [ h.disconnect() for h in self.active_handlers ]
        if self.username in dogs:
            del dogs[self.username]
        logging.info("Bye, %s!" % self.username)

    @classmethod
    def find(self, username):
        return dogs.get(username, None)

def process_command(handler, username, command):
    dog = Dog.find(username)
    if dog == None:
        logging.warning("Can't find %s for executing %s" % (username, command))
        return "ERROR!" # FIXME
    dog.send_command(command, handler)

def connection_ready(sock, fd, events):
    while True:
        try:
            connection, address = sock.accept()
        except socket.error, e:
            if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            return
        connection.setblocking(0)
        stream = iostream.IOStream(connection)

        dog = Dog(stream)
        # The first thing a Dog will send is its username. Catch it!
        stream.read_until(EOS, dog.setup)

nbr = 0
def assign_nbr():
    global nbr
    nbr = nbr + 1
    return str(nbr)

class HTTPHandler(web.RequestHandler):
    @web.asynchronous
    def get(self, username):
        dog = Dog.find(username)
        if dog == None:
            logging.warning("Someone tried to access %s, but it's not connected" % username)
            return
        self.dog = dog
        # a HTTP connection can be reused so don't add it more than once
        if self not in dog.active_handlers:
            dog.active_handlers.append(self)
            self.nbr = assign_nbr()

        if 'AlbumArt' in self.request.uri:
            uri = urllib.unquote(self.request.uri.decode('utf-8'))
            components = urlparse.urlsplit(uri)
            arguments = cgi.parse_qs(components.query)
            artist = arguments.get('artist', ['noneXYZ'])[0]
            album = arguments.get('album', ['noneXYZ'])[0]
            albumart = albumart_api.AlbumArt(self.albumart_callback)
            albumart.fetch(artist, album, 0)
        else:
            command = self.request.uri[len(username)+1:]
            process_command(self, username, command)

    def albumart_callback(self, data):
        self.send_result(RAW_YES, data)

    def send_result(self, raw, data):
        self.set_header("Content-Length", len(data))
        if raw == RAW_YES:
            self.set_header("Content-Type", "image/jpeg")
        else:
            self.set_header("Content-Type", "text/javascript")

        try:
            self.write(data)
            self.finish()
        except IOError:
            logging.warning("Could not write to HTTP client %s" % self.nbr)
            # handler will be removed later when called active()
            return

    def active(self):
        return not self._finished

    def disconnect(self):
        pass # HTTP clients will time out on their own

class WSHandler(websocket.WebSocketHandler):
    def open(self, username):
        self.username = username
        self.nbr = assign_nbr()
        dog = Dog.find(username)
        if dog == None:
            logging.debug("Someone tried to access %s, but it's not connected" % username)
            self.disconnect()
            return
        dog.active_handlers.append(self)
        self.receive_message(self.on_message)

    def on_message(self, command):
        process_command(self, self.username, command)
        try:
            self.receive_message(self.on_message)
        except IOError:
            logging.debug("Websocket read failed for %s: %s" % (self.username, command))
            self.disconnect()
            return

    def send_result(self, raw, data):
        try:
            self.write_message(data)
        except IOError:
            logging.debug("Websocket write failed for %s: %s" % (self.username, data))
            self.disconnect()
            return

    def active(self):
        return not self._finished

    def disconnect(self):
        self._finished = False
        self.close()

def setup_dog_socket(io_loop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(("", 8080))
    sock.listen(5000)

    callback = functools.partial(connection_ready, sock)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)

class ClientGenerator(web.OutputTransform):
    def __init__(self, request):
        self.request = request

    def transform_headers(self, headers):
        self.host = "dummy"
        if "dogbone-modules.js" in self.request.uri:
            u = self.request.uri.split('/')
            if len(u) >= 2:
                self.username = u[1]
            else:
                self.username = None
                return

            db_dog = db.get("SELECT * FROM dogs WHERE username = %s", self.username)
            if db_dog == None:
                self.username = None
                return block
            self.host = db_dog.host.encode('utf-8') + ":" + str(options.port) + "/api"
            len_diff = len(self.host) - len("dogvib.es:8080") + len(self.username)
            headers['Content-Length'] = int(headers['Content-Length']) + len_diff
        return headers

    def transform_chunk(self, block):
        if "dogbone-modules.js" in self.request.uri and self.username != None:
            block = block.replace('defaultUser: ""',
                                  'defaultUser: "%s"' % self.username)
            block = block.replace('defaultServer: "dogvib.es:8080"',
                                  'defaultServer: "%s"' % self.host)
        return block

    def footer(self):
        return None

if __name__ == '__main__':
    tornado.options.parse_command_line()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    db = database.Connection(options.mysql_host, options.mysql_database,
                             options.mysql_user, options.mysql_password)

    io_loop = ioloop.IOLoop.instance()
    setup_dog_socket(io_loop)

    http_server = httpserver.HTTPServer(Application())
    http_server.listen(options.port)

    print "Dogvibes API server started at port %d" % options.port

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
