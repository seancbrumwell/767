import tornado.web
import docparser


''' Main Handler class - renders an index.html file that then uses javascript
    and ajax to call back with the query/search parameters '''

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        self.set_header("Content-Type", "text/html")
        self.write(docparser.runQuery(self.get_argument('query').lower().split()))
