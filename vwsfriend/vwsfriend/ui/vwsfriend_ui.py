import threading
import os
import logging
import flask

from werkzeug.serving import make_server

import vwsfriend.ui.status as status

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "ERROR"

LOG = logging.getLogger("VWsFriend")


class VWsFriendUI:
    def __init__(self):
        print(os.path.dirname(__file__))
        self.app = flask.Flask('VWsFriend', template_folder=os.path.dirname(__file__)+'/templates', static_folder=os.path.dirname(__file__)+'/static')
        self.app.add_url_rule('/', '/', self.test, methods=['GET'])

        self.app.register_blueprint(status.bp)


    def run(self, host="0.0.0.0", port=4000, loglevel=logging.INFO):  # nosec
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        log = logging.getLogger('werkzeug')
        log.setLevel(loglevel)

        server = make_server(host, port, self.app)

        webthread = threading.Thread(target=server.serve_forever)
        webthread.start()
        LOG.info('VWsFriend is listening on %s:%s)', host, port)

        #server.shutdown()
        #webthread.join()
        #LOG.info('ProSafeExporter was stopped')
    
    def test(self):
        return flask.Response('laladede')
