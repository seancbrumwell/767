import tornado.web
import docparser
import settings
import os


''' Document Handler class - renders the requested document
h'''
class DocHandler(tornado.web.RequestHandler):
    def get(self, address):
        try:
            local_html = os.path.dirname(__file__)
            self.set_header("Content-Type", "text/html")
            try:
                myfile = open(local_html + "/templates/docs/" + address, "r")
                data = myfile.read()
                self.write(data)
            except:
                self.write("File Not Found")

        except Exception, e:
            print e
