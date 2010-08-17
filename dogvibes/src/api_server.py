import tornado.ioloop
import tornado.web
import errno
import functools
import socket
from tornado import ioloop, iostream, httpserver, websocket
import tornado.auth
import albumart_api
import logging
import cgi
import urlparse
import urllib

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

class Dog():
    def __init__(self, stream):
        self.stream = stream
        self.active_handlers = []

    def set_username(self, username):
        username = username[:-len(EOS)]
        dog = Dog.find(username)
        if dog != None:
            dog.destroy()
        dogs[username] = self

        logging.info("Welcome, %s!" % username)
        self.username = username

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

    def send_command(self, command, handler, login, avatar_url):
        try:
            # FIXME: UnicodeEncodeError: 'ascii' codec can't encode character u'\xf6' in position 46: ordinal not in range(128)
            self.stream.write(handler.nbr + SEP + command + SEP + login + SEP + avatar_url + EOS)
        except:
            logging.debug("Failed writing %s to Dog %s" % (command, self.username))
            self.destroy()
            return

        if not self.stream.reading():
            self.stream.read_until(EOS, self.command_callback)

    def destroy(self):
        self.stream.close()
        for handler in self.active_handlers:
            handler.disconnect()
        if dogs.has_key(self.username):
            del dogs[self.username]
        logging.info("Bye, %s!" % self.username)

    @classmethod
    def find(self, username):
        #if dogs.has_key(username), is this faster?
        try:
            return dogs[username]
        except:
            return None

def process_command(handler, username, command, login, avatar_url):
    dog = Dog.find(username)
    if dog == None:
        logging.warning("Can't find %s for executing %s" % (username, command))
        return "ERROR!" # FIXME
    dog.send_command(command, handler, login, avatar_url)

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
        stream.read_until(EOS, dog.set_username)

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/javascript")
        callback = self.get_argument("callback", None)
        twitter_name = self.get_secure_cookie("twitter_name")
        if not twitter_name:
            if callback:
                self.write("%s({'error': 5})" % callback)
            else:
                self.write("{'error': 5}")
            return
        twitter_avatar = self.get_secure_cookie("twitter_avatar")
        if callback:
            self.write("%s({'error':0,'result':{'username':'%s','avatar':'%s'}})" % (callback, twitter_name, twitter_avatar))
        else:
            self.write("{'error':0,'result':{'username':'%s','avatar':'%s'}}" % (twitter_name, twitter_avatar))

#
# Authorize agains Twitter.com
#
class TwitterHandler(tornado.web.RequestHandler,
                     tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self, username):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        referer = self.request.headers.get('Referer', None)
        self.clear_cookie("referer")
        if referer and "api.twitter.com" not in referer:
            self.set_cookie("referer", referer)
        self.authorize_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        logging.info("@%s authorized" % user["username"])
        self.set_secure_cookie("twitter_name", user["username"])
        self.set_secure_cookie("twitter_avatar", user["profile_image_url"])
        referer = self.get_cookie("referer")
        if referer:
            self.redirect(self.get_cookie("referer"))
        else:
            self.write("Congratulations, @%s is now authorized" % user["username"])
            self.finish()

nbr = 0
def assign_nbr():
    global nbr
    nbr = nbr + 1
    return str(nbr)

class HTTPHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, username):
        self.login = self.get_secure_cookie("twitter_name")
        if not self.login:
            self.login = "anonymous"
#            print "Not authorized"
#            return
        self.avatar_url = self.get_secure_cookie("twitter_avatar")
        if not self.avatar_url:
            self.avatar_url = "http://forums.azbilliards.com/images/cavatars/avatar5699_6.gif"

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
            process_command(self, username, command, self.login, self.avatar_url)

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
        self.login = self.get_secure_cookie("twitter_name")
        if not self.login:
            self.login = "anonymous"
#            print "Not authorized"
#            self.disconnect()
#            return
        self.avatar_url = self.get_secure_cookie("twitter_avatar")
        if not self.avatar_url:
            self.avatar_url = "http://forums.azbilliards.com/images/cavatars/avatar5699_6.gif"

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
        process_command(self, self.username, command, self.login, self.avatar_url)
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


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/getLoginInfo/*", LoginHandler), # TODO: split only on '/', avoids favicon
            (r"/authTwitter/([a-zA-Z0-9]+).*", TwitterHandler), # TODO: split only on '/', avoids favicon
            (r"/stream/([a-zA-Z0-9]+).*", WSHandler),
            (r"/([a-zA-Z0-9]+).*", HTTPHandler), # TODO: split only on '/', avoids favicon
        ]
        settings = dict(
            cookie_secret="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            twitter_consumer_key = "zLeTJ3Mvf0FkN3UzV3TrQ",
            twitter_consumer_secret = "QELveQpo4FaNhKi8A3cv5O0hW1i7Uiaas8hvYieY",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
#    logging.basicConfig(level=log_level, filename=options.log_file,
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    io_loop = ioloop.IOLoop.instance()
    setup_dog_socket(io_loop)

    http_server = httpserver.HTTPServer(Application())
    http_server.listen(80)

    print "Dogvibes API server started"

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
