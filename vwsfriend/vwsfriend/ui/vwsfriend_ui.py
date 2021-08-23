import threading
import os
import uuid
import logging
import flask

from flask_wtf.csrf import CSRFProtect

from werkzeug.serving import make_server

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vwsfriend.model.base import Base

import vwsfriend.ui.status as status
import vwsfriend.ui.settings as settings

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "ERROR"

LOG = logging.getLogger("VWsFriend")

csrf = CSRFProtect()


class VWsFriendUI:
    def __init__(self, weConnect=None, connector=None, dbUrl=None):
        print(os.path.dirname(__file__))
        self.app = flask.Flask('VWsFriend', template_folder=os.path.dirname(__file__) + '/templates', static_folder=os.path.dirname(__file__) + '/static')
        self.app.debug = True
        self.app.config.from_mapping(
            SECRET_KEY=uuid.uuid4().hex,
        )
        csrf.init_app(self.app)

        self.app.add_url_rule('/', '/', self.root)

        self.app.register_blueprint(status.bp)
        self.app.register_blueprint(settings.bp)
        self.app.weConnect = weConnect
        self.app.connector = connector

        if connector.withDB and dbUrl is not None:
            engine = create_engine(dbUrl)
            self.app.session = Session(engine)
            Base.metadata.create_all(engine)

    def run(self, host="0.0.0.0", port=4000, loglevel=logging.INFO):  # nosec
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        log = logging.getLogger('werkzeug')
        log.setLevel(loglevel)

        server = make_server(host, port, self.app)

        webthread = threading.Thread(target=server.serve_forever)
        webthread.start()
        LOG.info('VWsFriend is listening on %s:%s)', host, port)

        # server.shutdown()
        # webthread.join()
        # LOG.info('ProSafeExporter was stopped')

    def root(self):
        return flask.redirect(flask.url_for('status.vehicles'))
