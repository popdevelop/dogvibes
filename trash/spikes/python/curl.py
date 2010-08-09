import sys
import pycurl # requires deb python-curl
import json # requires deb python-json

class Test:
    def __init__(self):
        self.contents = ''

    def body_callback(self, buf):
        self.contents = self.contents + buf

t = Test()
c = pycurl.Curl()
c.setopt(c.URL, 'http://dogvibes.com:2000/amp/0/getStatus')
c.setopt(c.WRITEFUNCTION, t.body_callback)
c.perform()
c.close()

j = json.read(t.contents)
if j['error'] == 0:
    print j['status']
else:
    print 'Something went wrong!'
