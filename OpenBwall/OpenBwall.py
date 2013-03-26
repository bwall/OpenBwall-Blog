import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json
import threading
import time

from threading import Lock
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

posts = {}
lock = Lock()

class CSSHandler(tornado.web.RequestHandler):
    def get(self, id):
        cssFile = "body {background: white; color: black; margin:0px;}\body, input, textarea { font-family: Georgia, serif; font-size: 12pt; }\
        table { border-collapse: collapse; border: 0;} td { border: 0; padding: 0;} h1 {display:block; background-color: #f3f3f3; padding:10px; margin:0 0 10px 0;  color: #4183c4; text-decoration: none;}\
        h1, h2, h3, h4 { font-family: \"Helvetica Nue\", Helvetica, Arial, sans-serif; } h1 { font-size: 20pt;} pre, code { font-family: monospace; color: #060;} \
        pre { margin-left: 1em;  padding-left: 1em; border-left: 1px solid silver; line-height: 14pt;} a, a code { color: #00c;} #header { margin-bottom:10px; } \
        #header, #header a { color: #4183c4;} #header h1 a { text-decoration: none; } #footer { margin-left: 10px; margin-right: 10px;} #footer { margin-top: 3em;}\
        #content {width:100%; margin:0 auto;} .post {width:75%; margin:20px; margin:5px 5px 20px 5px; border: dotted #000 1px; padding:0px;} .post h2 {margin-top:0px;}\
        .post h2 a { display:block; background-color: #f3f3f3; padding:10px; margin:0 0 10px 0;  color: #4183c4; text-decoration: none;} #sidebar {padding:0px;float:right;width:24%;border: dotted #000 1px;display:table;}\
        .entry .date { margin-top: 3px;} .entry p { margin: 0; margin-bottom: 1em;} .entry .body { margin-top: 1em; line-height: 16pt;}"
        self.write(cssFile)

def GenerateHead(title):
    return "<html>\r\n<head>\r\n<title>" + title + "</title>\r\n<link href=\"/css/onlylamerslookatthis.css\" rel=\"stylesheet\" type=\"text/css\" media=\"all\"/>\r\n \
                    </head>\r\n<body>\r\n<div id=\"header\"><div style=\"float:right\"><a href=\"https://twitter.com/bwallHatesTwits\" title=\"@bwallHatesTwits on Twitter\">Have fun stalking me on Twitter</a></div>\r\n<h1>\
                    <a href=\"/\">OpenBwall: Read Access to bwall's Thoughts</a></h1></div>\r\n<div id=\"content\">"

def GenerateMarkovDiv():
    return "<script type=\"text/javascript\">\r\n\
function loadXMLDoc()\r\n\
{\r\n\
var xmlhttp;\r\n\
if (window.XMLHttpRequest)\r\n\
  {\r\n\
  xmlhttp=new XMLHttpRequest();\r\n\
  }\r\n\
else\r\n\
  {\r\n\
  xmlhttp=new ActiveXObject(\"Microsoft.XMLHTTP\");\r\n\
  }\r\n\
xmlhttp.onreadystatechange=function()\r\n\
  {\r\n\
  if (xmlhttp.readyState==4 && xmlhttp.status==200)\r\n\
    {\r\n\
    document.getElementById(\"markovOutput\").innerHTML=\"<b>Buckey:</b> \" + xmlhttp.responseText;\r\n\
    document.getElementById(\"markovInput\").value = \"\";\r\n\
    }\r\n\
  }\r\n\
xmlhttp.open(\"POST\",\"/api/markov/query\",true);\r\n\
xmlhttp.setRequestHeader(\"Content-type\",\"application/x-www-form-urlencoded\");\r\n\
xmlhttp.send(\"input=\" + encodeURIComponent(document.getElementById(\"markovInput\").value));\r\n\
document.getElementById(\"markovInput\").value = \"Response coming...\";\r\n\
}\r\n\
function handleKeyPress(e,form){\r\n\
var key=e.keyCode || e.which;\r\n\
if (key==13){\r\n\
loadXMLDoc();\r\n\
}\r\n\
}\r\n\
</script>\r\n\
<h3>Talk with Buckey</h3>\r\n\
<input type=\"text\" id=\"markovInput\" value=\"Talk to my AI here\" onkeypress=\"handleKeyPress(event,this.form)\" />\r\n\
<button type=\"button\" onclick=\"loadXMLDoc()\">Request response</button>\r\n\
<div id=\"markovOutput\"></div>\r\n"

def GenerateSideBar():
    global lock, posts
    sidebar = "<div id=\"sidebar\"><center><h3>All Posts</h3></center>"
    
    lock.acquire()
    for urlname in posts["order"]:
        entry = posts["posts"][urlname]
        sidebar += "<a href=\"/entry/" + urlname + "\" title=\"" + entry["title"] + "\">" + "[" + entry["date"] + "] " + entry["title"] + "</a>" + "<br>"
    lock.release()

    sidebar += GenerateMarkovDiv()

    sidebar += "</div>"
    return sidebar

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        global lock, posts
        homePage = GenerateHead("OpenBwall: Read Access to bwall's Thoughts") + GenerateSideBar()

        lock.acquire()
        
        for urlname in posts["order"]:
            entry = posts["posts"][urlname]
            homePage += "<div class=\"post\"><h2><a href=\"/entry/" + urlname + "\">" + entry["title"] + "</a></h2><div class=\"entry\"><div class=\"date\">" + entry["date"] + "</div>"
            homePage += "<div class=\"body\">" + entry["body"] + "</div></div></div>"
        
        lock.release()
        
        homePage += "</div></body></html>"
        self.write(homePage)

class EntryHandler(tornado.web.RequestHandler):
    def get(self, urlname):
        global lock, posts
        entry = False
        lock.acquire()
        if urlname in posts["posts"]:
            entry = posts["posts"][urlname]
        lock.release()
        if entry == False:
            raise tornado.web.HTTPError(404)

        homePage = GenerateHead("OpenBwall: " + entry["title"]) + GenerateSideBar()
        homePage += "<div class=\"post\"><h2><a href=\"/entry/" + urlname + "\">" + entry["title"] + "</a></h2><div class=\"entry\"><div class=\"date\">" + entry["date"] + "</div>"
        homePage += "<div class=\"body\">" + entry["body"] + "</div></div></div>"
        #tail end
        homePage += "</div></body></html>"
        self.write(homePage)

application = tornado.web.Application([
                                       (r"/", HomeHandler),
                                       (r"/css/(.*)", CSSHandler),
                                       (r"/entry/(.+)", EntryHandler),
                                       ])

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

def writePosts():
    global lock, posts
    lock.acquire()
    f = open('posts.json', 'r')
    posts = json.loads(f.read())
    f.close()    
    lock.release()
    
class UpdateThread(threading.Thread):
    def run(self):
        while True:
            writePosts()
            time.sleep(5)
            

if __name__ == "__main__":
    writePosts()
    t = UpdateThread()
    t.start()
    main()