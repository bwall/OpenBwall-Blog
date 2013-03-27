import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json
import threading
import time
import httplib
import hashlib

from threading import Lock
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

posts = {}
lock = Lock()
lastupdate = False

cssFile = False
pageTemplate = False
sideTemplate = False
postTemplate = False

class CSSHandler(tornado.web.RequestHandler):
    def get(self, id):
        global lock, cssFile
        lock.acquire()
        self.write(cssFile)
        lock.release()

def GeneratePage(title, content, description, keywords):
    global lock, pageTemplate, sideTemplate, posts
    lock.acquire()
    toReturn = ""
    try:
        sidebar = ""
        for urlname in posts["order"]:
            entry = posts["posts"][urlname]
            sidebar += sideTemplate % {"urlname" : urlname, "title" : entry["title"], "date" : entry["date"]}
        toReturn = pageTemplate % {"title" : title, "sidebar": sidebar, "content" : content, "description" : description, "keywords" : keywords}
    except:
        toReturn = "error"
    lock.release()
    return toReturn

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        global lock, posts, postTemplate

        lock.acquire()
        title = posts["title"]
        content = ""
        for urlname in posts["order"]:
            entry = posts["posts"][urlname]
            content += postTemplate % {"urlname" : urlname, "title" : entry["title"], "date" : entry["date"], "body" : entry["body"]}
        
        description = posts["description"]
        keywords = posts["keywords"]
        lock.release()

        self.write(GeneratePage(title, content, description, keywords))

class EntryHandler(tornado.web.RequestHandler):
    def get(self, urlname):
        global lock, posts, postTemplate
        entry = False
        lock.acquire()
        if urlname in posts["posts"]:
            entry = posts["posts"][urlname]
        lock.release()
        if entry == False:
            raise tornado.web.HTTPError(404)

        lock.acquire()
        content = postTemplate % {"urlname" : urlname, "title" : entry["title"], "date" : entry["date"], "body" : entry["body"]}
        description = entry["description"]
        keywords = entry["keywords"]
        lock.release()

        self.write(GeneratePage("OpenBwall: " + entry["title"], content, description, keywords))

class RefreshHandler(tornado.web.RequestHandler):
    def get(self, refreshAuth):
        if hashlib.sha256(refreshAuth).hexdigest() == "f84dde2069f8011d6eedc8759e3f9ec4cfe9b24d92eb6c37a25da42de23c64cb":
            updatePosts()
            self.write("Updated")

application = tornado.web.Application([
                                       (r"/", HomeHandler),
                                       (r"/css/(.*)", CSSHandler),
                                       (r"/entry/(.+)", EntryHandler),
                                       (r"/refresh/(.*)", RefreshHandler),
                                       ])

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

def updatePosts():
    global lock, posts, lastupdate, cssFile, pageTemplate, sideTemplate, postTemplate
    lock.acquire()
    if lastupdate == False or (time.mktime(time.gmtime()) - time.mktime(lastupdate)) > 300:
        try:
            conn = httplib.HTTPSConnection("raw.github.com")
            conn.request("GET", "/bwall/OpenBwall-Blog/master/OpenBwall/data/posts.json")
            r1 = conn.getresponse()
            if r1.status == 200:
                posts = json.loads(r1.read())
            conn.close()

            conn = httplib.HTTPSConnection("raw.github.com")
            conn.request("GET", "/bwall/OpenBwall-Blog/master/OpenBwall/data/css/style.css")
            r1 = conn.getresponse()
            if r1.status == 200:
                cssFile = r1.read()
            conn.close() 

            conn = httplib.HTTPSConnection("raw.github.com")
            conn.request("GET", "/bwall/OpenBwall-Blog/master/OpenBwall/data/pageTemplate.html")
            r1 = conn.getresponse()
            if r1.status == 200:
                pageTemplate = r1.read()
            conn.close() 

            conn = httplib.HTTPSConnection("raw.github.com")
            conn.request("GET", "/bwall/OpenBwall-Blog/master/OpenBwall/data/sideTemplate.html")
            r1 = conn.getresponse()
            if r1.status == 200:
                sideTemplate = r1.read()
            conn.close() 

            conn = httplib.HTTPSConnection("raw.github.com")
            conn.request("GET", "/bwall/OpenBwall-Blog/master/OpenBwall/data/postTemplate.html")
            r1 = conn.getresponse()
            if r1.status == 200:
                postTemplate = r1.read()
            conn.close()
        except:
            print "Failed to update" 
    lock.release()

if __name__ == "__main__":
    updatePosts()
    main()