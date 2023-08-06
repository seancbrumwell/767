import tornado.web
import docparser


''' Main Handler class - renders an index.html file that then uses javascript
    and ajax to call back with the query/search parameters '''

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        self.set_header("Content-Type", "text/html")

        if self.get_argument('searchType') == 'vector':
            self.write(docparser.runQuery(self.get_argument('query').lower().split()))
        else:
            self.write(docparser.runBooleanQuery(self.get_argument('query').lower().split()))
