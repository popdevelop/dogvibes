import BaseHTTPServer
from urlparse import urlparse

class API:
    def getStatus(self, query):
        return "In getStatus: " + query

class APIHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        api = API()
        u = urlparse(self.path)
        method = u.path.split('/')[-1]
        if hasattr(api, method):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = getattr(api, method).__call__(u.query)
            self.wfile.write(data)
        else:
            self.send_error(404, 'Unsupported call')

httpserver = BaseHTTPServer.HTTPServer(("", 2000), APIHandler)
httpserver.serve_forever()
