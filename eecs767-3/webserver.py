import tornado.ioloop
import tornado.web
import tornado.httpserver
import docparser
from mainhandler import MainHandler
from dochandler import DocHandler
from datetime import datetime
import server_config
import settings


def refreshDocs():
    print "Refreshing Document Information - %s" % datetime.now().strftime("%Y-%m-%d %H:%M")
    docparser.doc_totals = docparser.parseDocs(server_config.document_path)

settings = {
            "template_path": settings.TEMPLATE_PATH,
            "static_path": settings.STATIC_PATH,
            "autoreload": True
        }

application = tornado.web.Application(
        [
        (r"/", MainHandler),
        (r"/docs/(.*)", DocHandler),
        ],  **settings)


if __name__ == "__main__":
    try:
        docparser.doc_totals = docparser.parseDocs(server_config.document_path)
        main_loop = tornado.ioloop.IOLoop.instance()
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(server_config.server_port)
        scheduler = tornado.ioloop.PeriodicCallback(refreshDocs,server_config.refresh_rate, io_loop = main_loop)
        scheduler.start()
        main_loop.start()

    except KeyboardInterrupt:
        scheduler.stop()
        main_loop.stop()
        print "\nProgram Terminated"
