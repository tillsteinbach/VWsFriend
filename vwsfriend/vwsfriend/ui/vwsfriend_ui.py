import base64
import threading
import time
import os
import sys
import uuid
import logging
import flask
import flask_login

import sqlalchemy

from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import Length

from werkzeug.serving import make_server

from vwsfriend.model.base import Base

from vwsfriend.model.settings import Settings

import vwsfriend.ui.status as status
import vwsfriend.ui.settings as settings
import vwsfriend.ui.database as database

from vwsfriend.ui.cache import cache

from vwsfriend.__version import __version__ as __vwsfriend_version__
from weconnect.__version import __version__ as __weconnect_version__

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "ERROR"

LOG = logging.getLogger("VWsFriend")

csrf = CSRFProtect()


class LoginForm(FlaskForm):
    username = StringField('User', validators=[Length(min=1, max=255)])
    password = PasswordField('Password')
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')


class VWsFriendUI:
    def __init__(self, weConnect=None, connector=None, homekitDriver=None, dbUrl=None, configDir=None, username=None, password=None):  # noqa: C901
        self.app = flask.Flask('VWsFriend', template_folder=os.path.dirname(__file__) + '/templates', static_folder=os.path.dirname(__file__) + '/static')
        self.app.debug = True
        self.app.config.from_mapping(
            SECRET_KEY=uuid.uuid4().hex,
        )
        csrf.init_app(self.app)

        cache.init_app(self.app)

        loginManager = flask_login.LoginManager()
        loginManager.init_app(self.app)
        loginManager.login_view = "login"
        loginManager.login_message = "You have to login to see this page"
        self.users = {}
        if username is not None and password is not None:
            self.users[username] = {'password': password}

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
        self.app.configDir = configDir

        if connector.withDB and dbUrl is not None:
            self.app.config['SQLALCHEMY_DATABASE_URI'] = dbUrl
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            self.app.db = SQLAlchemy(self.app)

            #  engine = create_engine(dbUrl)
            #  self.app.session = Session(engine)
            with self.app.app_context():
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
                result = self.app.db.session.execute(sqlalchemy.text('SELECT version_num FROM alembic_version LIMIT 1;')).fetchone()
                if result is not None and result:
                    flask.g.versions['Database Schema'] = result[0]
                else:
                    flask.g.versions['Database Schema'] = 'unknown'

                try:
                    result = self.app.db.session.execute(sqlalchemy.text('SELECT version();')).fetchone()
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

        @self.app.route('/restart', methods=['GET'])
        @flask_login.login_required
        def restart():
            def delayed_restart():
                time.sleep(10)
                python = sys.executable
                os.execl(python, python, * sys.argv)  # nosec

            t = threading.Thread(target=delayed_restart)
            t.start()
            return flask.redirect(flask.url_for('restartrefresh'))

        @self.app.route('/restartrefresh', methods=['GET'])
        def restartrefresh():
            return flask.render_template('restart.html', current_app=flask.current_app)

        @loginManager.user_loader
        def user_loader(username):
            if username not in self.users:
                return

            user = flask_login.UserMixin()
            user.id = username
            return user

        @loginManager.request_loader
        def load_user_from_request(request):
            auth = request.headers.get('Authorization')
            if auth and 'Basic ' in auth:
                auth = auth.replace('Basic ', '', 1)
                try:
                    auth = base64.b64decode(auth).decode("utf-8")
                except TypeError:
                    return None
                if ':' in auth:
                    userPass = auth.split(":", 1)
                    if userPass[0] in self.users and 'password' in self.users[userPass[0]] and userPass[1] == self.users[userPass[0]]['password']:
                        user = flask_login.UserMixin()
                        user.id = userPass[0]
                        return user
            # finally, return None if both methods did not login the user
            return None

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            form = LoginForm()

            if form.validate_on_submit():
                username = form.username.data
                if username in self.users and 'password' in self.users[username] and form.password.data == self.users[username]['password']:
                    user = flask_login.UserMixin()
                    user.id = username
                    remember = form.remember_me.data
                    flask_login.login_user(user, remember=remember)

                    next = flask.request.args.get('next', default='status/vehicles')
                    return flask.redirect(next)
                else:
                    form.password.data = ''
                    flask.flash('User unknown or password is wrong')

            return flask.render_template('login/login.html', form=form, current_app=self.app)

        @self.app.route("/logout")
        @flask_login.login_required
        def logout():
            flask_login.logout_user()
            return flask.redirect('login')

    def run(self, host="0.0.0.0", port=4000, loglevel=logging.INFO):  # nosec
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'
        log = logging.getLogger('werkzeug')
        log.setLevel(loglevel)

        server = make_server(host, port, self.app, threaded=True)

        webthread = threading.Thread(target=server.serve_forever)
        webthread.start()
        LOG.info('VWsFriend is listening on %s:%s)', host, port)
