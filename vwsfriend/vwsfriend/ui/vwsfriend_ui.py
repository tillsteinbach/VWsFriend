import threading
import os
import uuid
import logging
import flask

import sqlalchemy

from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

from werkzeug.serving import make_server

from vwsfriend.model.base import Base

from vwsfriend.model.settings import Settings

import vwsfriend.ui.status as status
import vwsfriend.ui.settings as settings
import vwsfriend.ui.database as database

from vwsfriend.__version import __version__ as __vwsfriend_version__
from weconnect.__version import __version__ as __weconnect_version__

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "ERROR"

LOG = logging.getLogger("VWsFriend")

csrf = CSRFProtect()


class VWsFriendUI:
    def __init__(self, weConnect=None, connector=None, homekitDriver=None, dbUrl=None):  # noqa: C901
        self.app = flask.Flask('VWsFriend', template_folder=os.path.dirname(__file__) + '/templates', static_folder=os.path.dirname(__file__) + '/static')
        self.app.debug = True
        self.app.config.from_mapping(
            SECRET_KEY=uuid.uuid4().hex,
        )
        csrf.init_app(self.app)

        class NoHealth(logging.Filter):
            def filter(self, record):
                return 'GET /healthcheck' not in record.getMessage()

        #  Disable logging for healthcheck
        logging.getLogger("werkzeug").addFilter(NoHealth())

        self.app.register_blueprint(status.bp)
        self.app.register_blueprint(settings.bp)
        if connector.withDB:
            self.app.register_blueprint(database.bp)
        self.app.weConnect = weConnect
        self.app.connector = connector
        self.app.homekitDriver = homekitDriver

        if connector.withDB and dbUrl is not None:
            self.app.config['SQLALCHEMY_DATABASE_URI'] = dbUrl
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            self.app.db = SQLAlchemy(self.app)

            #  engine = create_engine(dbUrl)
            #  self.app.session = Session(engine)
            Base.metadata.create_all(self.app.db.get_engine())

        @self.app.before_request
        def before_request_callback():
            flask.g.versions = dict()
            flask.g.versions['VWsFriend'] = __vwsfriend_version__
            flask.g.versions['WeConnect Python Library'] = __weconnect_version__
            if self.app.connector.withDB:
                flask.g.dbsettings = self.app.db.session.query(Settings).first()

        @self.app.route('/', methods=['GET'])
        def root():
            if flask.current_app.connector.withDB and flask.g.dbsettings is None:
                return flask.redirect(flask.url_for('database.settingsEdit'))
            return flask.redirect(flask.url_for('status.vehicles'))

        @self.app.route('/versions', methods=['GET'])
        def versions():
            if flask.current_app.connector.withDB:
                result = self.app.db.session.execute('SELECT version_num FROM alembic_version LIMIT 1;').fetchone()
                if result is not None and result:
                    flask.g.versions['Database Schema'] = result[0]
                else:
                    flask.g.versions['Database Schema'] = 'unknown'

                try:
                    result = self.app.db.session.execute('SELECT version();').fetchone()
                    if result is not None and result:
                        flask.g.versions['Database'] = result[0]
                    else:
                        flask.g.versions['Database'] = 'unknown'
                except sqlalchemy.exc.OperationalError:
                    pass

            return flask.render_template('versions.html', current_app=flask.current_app)

        @self.app.route('/healthcheck', methods=['GET'])
        def healthcheck():
            return 'ok'

    def run(self, host="0.0.0.0", port=4000, loglevel=logging.INFO):  # nosec
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        log = logging.getLogger('werkzeug')
        log.setLevel(loglevel)

        server = make_server(host, port, self.app, threaded=True)

        webthread = threading.Thread(target=server.serve_forever)
        webthread.start()
        LOG.info('VWsFriend is listening on %s:%s)', host, port)
