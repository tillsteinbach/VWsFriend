import os
import sys
import re
import argparse
from datetime import datetime, timedelta, timezone
import logging
import logging.handlers
import time
import tempfile
import netrc

import threading

from pyhap.accessory_driver import AccessoryDriver

from weconnect import weconnect
from weconnect.errors import APICompatibilityError, AuthentificationError, TemporaryAuthentificationError
from weconnect.util import DuplicateFilter
from weconnect.__version import __version__ as __weconnect_version__
from weconnect.domain import Domain

from vwsfriend.ui.vwsfriend_ui import VWsFriendUI
from vwsfriend.homekit.bridge import VWsFriendBridge
from vwsfriend.agent_connector import AgentConnector
from vwsfriend.privacy import Privacy

from vwsfriend.homekit.custom_characteristics import CUSTOM_CHARACTERISTICS

from .__version import __version__

SUPPORT_MQTT = False
try:
    from dateutil import tz
    import ssl

    from weconnect_mqtt. weconnect_mqtt_base import PictureFormat, WeConnectMQTTClient  # type: ignore
    from weconnect_mqtt.__version import __version__ as __weconnect_mqtt_version__
    import paho.mqtt.client
    SUPPORT_MQTT = True
except ImportError:
    pass

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "ERROR"

LOG = logging.getLogger("VWsFriend")


class NumberRangeArgument:

    def __init__(self, imin=None, imax=None):
        self.imin = imin
        self.imax = imax

    def __call__(self, arg):
        try:
            value = int(arg)
        except ValueError as e:
            raise self.exception() from e
        if (self.imin is not None and value < self.imin) or (self.imax is not None and value > self.imax):
            raise self.exception()
        return value

    def exception(self):
        if self.imin is not None and self.imax is not None:
            return argparse.ArgumentTypeError(f'Must be a number from {self.imin} to {self.imax}')
        if self.imin is not None:
            return argparse.ArgumentTypeError(f'Must be a number not smaller than {self.imin}')
        if self.imax is not None:
            return argparse.ArgumentTypeError(f'Must be number not larger than {self.imax}')

        return argparse.ArgumentTypeError('Must be a number')


def main():  # noqa: C901 pylint: disable=too-many-branches, too-many-statements, too-many-locals
    parser = argparse.ArgumentParser(
        prog='vwsfriend',
        description='TBD')
    if SUPPORT_MQTT:
        parser.add_argument('--version', action='version',
                            version=f'%(prog)s {__version__} (using WeConnect-python {__weconnect_version__}, WeConnect-mqtt {__weconnect_mqtt_version__})')
    else:
        parser.add_argument('--version', action='version',
                            version=f'%(prog)s {__version__} (using WeConnect-python {__weconnect_version__})')
    parser.add_argument('-u', '--username', help='Username of VWsFriend UI', required=False)
    parser.add_argument('-p', '--password', help='Password of VWsFriend UI', required=False)
    parser.add_argument('--host', help='Host of VWsFriend UI', type=str, required=False, default='0.0.0.0')  # nosec
    parser.add_argument('--port', help='Port of VWsFriend UI', type=int, choices=range(1, 65535), metavar="[1-65535]", required=False, default=4000)
    weConnectGroup = parser.add_argument_group('WeConnect')
    weConnectGroup.add_argument('--weconnect-username', dest='weConnectUsername', help='Username of Volkswagen id', required=False)
    weConnectGroup.add_argument('--weconnect-password', dest='weConnectPassword', help='Password of Volkswagen id', required=False)
    weConnectGroup.add_argument('--weconnect-spin', dest='weConnectSpin', help='S-PIN of Volkswagen id, required for selected commands in Homekit',
                                required=False, nargs='?', action='store', default=None, const=True)
    defaultNetRc = os.path.join(os.path.expanduser("~"), ".netrc")
    weConnectGroup.add_argument('--netrc', help=f'File in netrc syntax providing login (default: {defaultNetRc}).'
                                ' Netrc is only used when username and password are not provided  as arguments',
                                default=None, required=False)
    weConnectGroup.add_argument('-i', '--interval', help='Query interval in seconds',
                                type=NumberRangeArgument(imin=120), required=False, default=180)
    defaultTemp = os.path.join(tempfile.gettempdir(), 'weconnect.token')
    weConnectGroup.add_argument('--tokenfile', help=f'file to store token (default: {defaultTemp})', default=defaultTemp)
    weConnectGroup.add_argument('--no-token-storage', dest='noTokenStorage', help='Do not store token on filesystem (this'
                                ' will cause a new login for every invokation!)', action='store_true')

    parser.add_argument('--config-dir', dest='configDir', help='directory to store configuration files (default: ./)', default='./')
    parser.add_argument('--demo', help='folder containing demo scenario, see README for more information')
    parser.add_argument('--privacy', help='Options to control privacy of the cars users', default=[], required=False, action='append',
                        type=Privacy, choices=list(Privacy))
    dbGroup = parser.add_argument_group('Database & visualization')

    dbGroup.add_argument('--with-database', dest='withDatabase', help='Connect VWsFriend to database for visualization', action='store_true')
    dbGroup.add_argument('--database-url', dest='dbUrl', help='Database to connect to', default='sqlite:///vwsfrienddevel.db')

    abrpGroup = parser.add_argument_group('ABRP: A better route planner')
    abrpGroup.add_argument('--with-abrp', dest='withABRP', help='Connect VWsFriend to ABRP (you need to add userTokens in the UI!)', action='store_true')

    homekitGroup = parser.add_argument_group('Homekit')
    homekitGroup.add_argument('--with-homekit', dest='withHomekit', help='Provide Apple Homekit functionality', action='store_true')
    homekitGroup.add_argument('--homekit-address', dest='homekitAddress', type=str, help='IP address used to listen on for Apple Homekit functionality',
                              default=None)
    homekitGroup.add_argument('--homekit-port', dest='homekitPort', help='Port used to listen on for Apple Homekit functionality', type=int,
                              choices=range(1, 65535), metavar="[1-65535]", required=False, default=51234)

    loggingGroup = parser.add_argument_group('Logging')
    loggingGroup.add_argument('-v', '--verbose', action="append_const", help='Logging level (verbosity)', const=-1,)
    loggingGroup.add_argument('--logging-format', dest='loggingFormat', help='Logging format configured for python logging '
                              '(default: %%(asctime)s:%%(levelname)s:%%(module)s:%%(message)s)', default='%(asctime)s:%(levelname)s:%(module)s:%(message)s')
    loggingGroup.add_argument('--logging-date-format', dest='loggingDateFormat', help='Logging format configured for python logging '
                              '(default: %%Y-%%m-%%dT%%H:%%M:%%S%%z)', default='%Y-%m-%dT%H:%M:%S%z')
    loggingGroup.add_argument('--hide-repeated-log', dest='hideRepeatedLog', help='Hide repeated log messages from the same module', action='store_true')

    loggingMailGroup = parser.add_argument_group('Logging to Email (Errors only)')
    loggingMailGroup.add_argument('--logging-mail-from', dest='loggingMailFrom', help='Mail address to send mails from', required=False)
    loggingMailGroup.add_argument('--logging-mail-to', dest='loggingMailTo', help='Mail address to send mails to (can be used multiple times)', required=False,
                                  action='append')
    loggingMailGroup.add_argument('--logging-mail-host', dest='loggingMailHost', help='Mail server host', required=False)
    loggingMailGroup.add_argument('--logging-mail-credentials', dest='loggingMailCredentials', help='Mail server credentials', required=False, nargs=2)
    loggingMailGroup.add_argument('--logging-mail-subject', dest='loggingMailSubject', help='Mail subject', required=False, default='VWsFriend Log')
    loggingMailGroup.add_argument('--logging-mail-notls', dest='loggingMailnotls', help='Mail do not use TLS', required=False, action='store_true')
    loggingMailGroup.add_argument('--logging-mail-testmail', dest='loggingMailTestmail', help='Try to send Testmail at startup', required=False,
                                  action='store_true')
    loggingMailGroup.add_argument('--logging-mail-filter-duplicates', dest='loggingMailFilterDuplicates', help='Filter duplicated messages out', required=False,
                                  action='store_true')
    loggingMailGroup.add_argument('--logging-mail-filter-reset', dest='loggingMailFilterReset', help='Reset duplicate filter after number of seconds', type=int,
                                  required=False, default=0)

    if SUPPORT_MQTT:
        mqttGroup = parser.add_argument_group('MQTT', description='MQTT support in VWsFriend is EXPERIMENTAL,'
                                              ' if you need stable MQTT support please see https://github.com/tillsteinbach/WeConnect-mqtt'
                                              ' --mqttbroker option must be set to enable MQTT')
        mqttGroup.add_argument('--mqttbroker', type=str, help='Address of MQTT Broker to connect to', required=False)
        mqttGroup.add_argument('--mqttport', type=NumberRangeArgument(1, 65535), help='Port of MQTT Broker. Default is 1883 (8883 for TLS)',
                               required=False, default=None)
        mqttGroup.add_argument('--mqttclientid', required=False, default=None, help='Id of the client. Default is a random id')
        mqttGroup.add_argument('--prefix', help='MQTT topic prefix (default is weconnect/0)', type=str, required=False, default='weconnect/0')
        mqttGroup.add_argument('-k', '--mqttkeepalive', required=False, type=int, default=60, help='Time between keep-alive messages')
        mqttGroup.add_argument('-mu', '--mqtt-username', type=str, dest='mqttusername', help='Username for MQTT broker', required=False)
        mqttGroup.add_argument('-mp', '--mqtt-password', type=str, dest='mqttpassword', help='Password for MQTT broker', required=False)
        mqttGroup.add_argument('-mv', '--mqtt-version', type=str, dest='mqttversion', help='MQTT protocol version used', required=False,
                               choices=['3.1', '3.1.1', '5'], default='3.1.1')
        mqttGroup.add_argument('--transport', required=False, default='tcp', choices=["tcp", 'websockets'],
                               help='EXPERIMENTAL support for websockets transport')
        mqttGroup.add_argument('-s', '--use-tls', action='store_true', help='EXPERIMENTAL')
        mqttGroup.add_argument('--insecure', action='store_true', help='EXPERIMENTAL')
        mqttGroup.add_argument('--cacerts', required=False, default=None, help='EXPERIMENTAL path to the Certificate Authority'
                               ' certificate files that are to be treated as trusted by this client')
        mqttGroup.add_argument('--cert', required=False, default=None, help='EXPERIMENTAL PEM encoded client certificate')
        mqttGroup.add_argument('--key', required=False, default=None, help='EXPERIMENTAL PEM encoded client private key')
        mqttGroup.add_argument('--tls-version', required=False, default=None, choices=['tlsv1.2', 'tlsv1.1', 'tlsv1'],
                               help='EXPERIMENTAL TLS protocol version')
        mqttGroup.add_argument('--ignore-for', dest='ignore', help='Ignore messages for first IGNORE seconds after subscribe to aviod '
                               'retained messages from the broker to make changes to the car (default is 5s) if you don\'t want this behavious set to 0',
                               type=int, required=False, default=5)
        mqttGroup.add_argument('--republish-on-update', dest='republishOnUpdate', action='store_true',
                               help='Republish all topics on every update, not just when the value changes.')
        mqttGroup.add_argument('--list-topics', dest='listTopics', help='List new topics when created the first time', action='store_true')
        mqttGroup.add_argument('--topic-filter-regex', dest='topicFilterRegexString', type=str,
                               default='<PREFIX>/vehicles/[0-9A-Z]+/domains/[a-zA-Z]+/[a-zA-Z]+/request/.*',
                               help='Filter topics by regex. Default is: "<PREFIX>/vehicles/[0-9A-Z]+/domains/[a-zA-Z]+/[a-zA-Z]+/request/.*"')

        mqttGroup.add_argument('--convert-times', dest='convertTimes',
                               help='Convert all times from UTC to timezone, e.g. --convert-times \'Europe/Berlin\', leave empty to use system timezone',
                               nargs='?', const='', default=None, type=str)
        mqttGroup.add_argument('--timeformat', dest='timeFormat',
                               help='Convert times using the timeformat provided default is ISO format, leave argument empty to use system default',
                               nargs='?', const='', default=None, type=str)
        mqttGroup.add_argument('--locale',
                               help='Use specified locale, leave argument empty to use system default', default='', type=str)
        mqttGroup.add_argument('--pictures', help='Add ASCII art pictures', action='store_true')
        mqttGroup.add_argument('--picture-format', dest='pictureFormat', help='Format of the picture topics', default=PictureFormat.TXT, required=False,
                               type=PictureFormat, choices=list(PictureFormat))
        mqttGroup.add_argument('--with-raw-json-topic', dest='withRawJsonTopic', help='Adds topic <PREFIX>/rawjson with all information in one json string.'
                               ' Topic is updated on change only', action='store_true')
        mqttGroup.add_argument('-l', '--chargingLocation', nargs=2, metavar=('latitude', 'longitude'), type=float,
                               help='If set charging locations will be added to the result around the given coordinates')
        mqttGroup.add_argument('--chargingLocationRadius', type=NumberRangeArgument(0, 100000),
                               help='Radius in meters around the chargingLocation to search for chargers')

    args = parser.parse_args()

    logLevel = LOG_LEVELS.index(DEFAULT_LOG_LEVEL)
    for adjustment in args.verbose or ():
        logLevel = min(len(LOG_LEVELS) - 1, max(logLevel + adjustment, 0))

    logging.basicConfig(level=LOG_LEVELS[logLevel], format=args.loggingFormat, datefmt=args.loggingDateFormat)
    logging.getLogger("pyhap").setLevel(level=LOG_LEVELS[logLevel])
    if args.hideRepeatedLog:
        for handler in logging.root.handlers:
            handler.addFilter(DuplicateFilter())
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if any(arg is not None for arg in [args.loggingMailFrom, args.loggingMailTo, args.loggingMailHost, args.loggingMailCredentials]):
        if all(arg is not None for arg in [args.loggingMailFrom, args.loggingMailTo, args.loggingMailHost, args.loggingMailCredentials]):
            secure = ()
            if args.loggingMailnotls:
                secure = None
            smtpHandler = logging.handlers.SMTPHandler(mailhost=args.loggingMailHost,
                                                       fromaddr=args.loggingMailFrom,
                                                       toaddrs=args.loggingMailTo,
                                                       subject=args.loggingMailSubject,
                                                       credentials=args.loggingMailCredentials,
                                                       secure=secure)
            smtpHandler.setLevel(logging.INFO)
            smtpHandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
            if args.loggingMailFilterDuplicates:
                smtpHandler.addFilter(DuplicateFilter(doNotFilterAbove=logging.CRITICAL, filterResetSeconds=args.loggingMailFilterReset))
            LOG.addHandler(smtpHandler)
            if args.loggingMailTestmail:
                if SUPPORT_MQTT:
                    msg = f'vwsfriend {__version__} (using WeConnect-python {__weconnect_version__}, WeConnect-mqtt {__weconnect_mqtt_version__})'
                else:
                    msg = f'vwsfriend {__version__} (using WeConnect-python {__weconnect_version__})'
                smtpHandler.emit(logging.LogRecord('VWsFriend', logging.INFO, pathname=None, lineno=None, msg=msg, args=None, exc_info=None))
            smtpHandler.setLevel(logging.ERROR)
        else:
            LOG.error('You need to provide all --logging-mail options to make mail work')
            sys.exit(1)

    if SUPPORT_MQTT:
        LOG.info('vwsfriend %s (using WeConnect-python %s, WeConnect-mqtt %s)', __version__, __weconnect_version__, __weconnect_mqtt_version__)
    else:
        LOG.info('vwsfriend %s (using WeConnect-python %s)', __version__, __weconnect_version__)

    username = None
    password = None

    if args.username is not None and args.password is not None:
        username = args.username
        password = args.password
    else:
        if args.netrc is not None:
            netRcFilename = args.netrc
        else:
            netRcFilename = defaultNetRc
        try:
            secrets = netrc.netrc(file=args.netrc)
            username, _, password = secrets.authenticators("VWsFriend")
        except netrc.NetrcParseError as err:
            LOG.error('Authentification using .netrc failed: %s', err)
            sys.exit(1)
        except TypeError:
            LOG.error('VWsFriend entry was not found in %s netrc-file. Create it or provide a username with --username and a password with --password'
                      ' with --username', netRcFilename)
            sys.exit(1)
        except FileNotFoundError:
            LOG.error('%s netrc-file was not found. Create it or provide a username with --username and a password with --password',
                      netRcFilename)
            sys.exit(1)

    if args.weConnectUsername is not None and args.weConnectPassword is not None:
        weConnectUsername = args.weConnectUsername
        weConnectPassword = args.weConnectPassword
    else:
        if args.netrc is not None:
            netRcFilename = args.netrc
        else:
            netRcFilename = defaultNetRc
        try:
            secrets = netrc.netrc(file=args.netrc)
            weConnectUsername, _, weConnectPassword = secrets.authenticators("volkswagen.de")
        except netrc.NetrcParseError as err:
            LOG.error('Authentification using .netrc failed: %s', err)
            sys.exit(1)
        except TypeError:
            weConnectUsername = username
            weConnectPassword = password
            LOG.warning('volkswagen.de entry was not found in %s netrc-file. Create it or provide a username with --weconnect-username and a password with'
                        ' --weconnect-password', netRcFilename)
        except FileNotFoundError:
            weConnectUsername = username
            weConnectPassword = password
            LOG.warning('%s netrc-file was not found. Create it or provide a username with --weconnect-username and a password with --weconnect-password',
                        netRcFilename)

    weConnectSpin = None
    if args.weConnectSpin is not None:
        weConnectSpin = args.weConnectSpin
    else:
        if args.netrc is not None:
            netRcFilename = args.netrc
        else:
            netRcFilename = defaultNetRc
        try:
            secrets = netrc.netrc(file=args.netrc)
            _, account, _ = secrets.authenticators("volkswagen.de")
            if account is not None:
                weConnectSpin = account
        except netrc.NetrcParseError as err:
            LOG.error('Authentification using .netrc failed: %s', err)
            sys.exit(1)
        except TypeError:
            pass
        except FileNotFoundError:
            pass
    if weConnectSpin is not None and not isinstance(weConnectSpin, bool):
        if len(weConnectSpin) == 0:
            weConnectSpin = None
        elif not re.match(r"^\d{4}$", weConnectSpin):
            LOG.error('S-PIN: %s needs to be a four digit number', weConnectSpin)
            sys.exit(1)

    tokenfile = None
    if not args.noTokenStorage:
        tokenfile = args.tokenfile

    weConnect = None
    mqttCLient = None
    try:  # pylint: disable=too-many-nested-blocks
        weConnect = weconnect.WeConnect(username=weConnectUsername, password=weConnectPassword, spin=weConnectSpin, tokenfile=tokenfile,
                                        updateAfterLogin=False, loginOnInit=(args.demo is None), maxAgePictures=86400, forceReloginAfter=21600, numRetries=5,
                                        timeout=180)

        connector = AgentConnector(weConnect=weConnect, dbUrl=args.dbUrl, interval=args.interval, withDB=args.withDatabase, withABRP=args.withABRP,
                                   configDir=args.configDir, privacy=args.privacy)

        driver = None
        if args.withHomekit:
            LOG.info('Starting up Homekit')
            # Start the accessory on port 51234
            driver = AccessoryDriver(address=args.homekitAddress, port=args.homekitPort, pincode=None, persist_file=f'{args.configDir}/accessory.state')

            for characteristicKey, characteristic in CUSTOM_CHARACTERISTICS.items():
                driver.loader.char_types[characteristicKey] = characteristic

            bridge = VWsFriendBridge(driver=driver, weConnect=weConnect, accessoryConfigFile=f'{args.configDir}/accessory.config')
            driver.add_accessory(bridge)
            weConnectBridgeInitialized = False

            # Start it!
            hapThread = threading.Thread(target=driver.start)
            hapThread.start()

            # Enable status tracking:
            weConnect.enableTracker()

        if SUPPORT_MQTT and args.mqttbroker:
            LOG.info('Starting up MQTT')
            usetls = args.use_tls
            if args.cacerts:
                usetls = True

            if args.mqttport is None:
                if usetls:
                    args.mqttport = 8883
                else:
                    args.mqttport = 1883

            mqttusername = None
            mqttpassword = None
            if args.mqttusername is not None:
                mqttusername = args.mqttusername
            if args.mqttpassword is not None:
                mqttpassword = args.mqttpassword

            if mqttusername is None and mqttpassword is None:
                if args.netrc is not None:
                    netRcFilename = args.netrc
                else:
                    netRcFilename = defaultNetRc
                try:
                    secrets = netrc.netrc(file=args.netrc)
                    authenticator = secrets.authenticators(args.mqttbroker)
                    if authenticator is not None:
                        mqttusername, _, mqttpassword = authenticator
                except FileNotFoundError:
                    if args.netrc is not None:
                        LOG.error('%s netrc-file was not found. Create it or provide at least a username with --username',
                                  netRcFilename)
                        sys.exit(1)

            try:
                topicFilterRegexString = args.topicFilterRegexString
                topicFilterRegexString.replace('<PREFIX>', args.prefix)
                topicFilterRegex = re.compile(args.topicFilterRegexString)
            except re.error as err:
                LOG.error('Problem with provided regex %s: %s', topicFilterRegexString, err)
                sys.exit(1)

            convertTimezone = None
            if args.convertTimes is not None:
                if args.convertTimes == '':
                    convertTimezone = datetime.now().astimezone().tzinfo
                else:
                    convertTimezone = tz.gettz(args.convertTimes)

            if args.chargingLocation is not None:
                latitude, longitude = args.chargingLocation
                if latitude < -90 or latitude > 90:
                    LOG.error('latitude must be between -90 and 90')
                    sys.exit(1)
                if longitude < -180 or longitude > 180:
                    LOG.error('longitude must be between -180 and 180')
                    sys.exit(1)
                weConnect.latitude = latitude
                weConnect.longitude = longitude
                weConnect.searchRadius = args.chargingLocationRadius

            if args.mqttversion == '3.1':
                mqttVersion = paho.mqtt.client.MQTTv31
            elif args.mqttversion == '5':
                mqttVersion = paho.mqtt.client.MQTTv5
            else:
                mqttVersion = paho.mqtt.client.MQTTv311

            mqttCLient = WeConnectMQTTClient(clientId=args.mqttclientid, protocol=mqttVersion, transport=args.transport, interval=args.interval,
                                             prefix=args.prefix, ignore=args.ignore, updateCapabilities=True, updatePictures=True,
                                             listNewTopics=args.listTopics, republishOnUpdate=args.republishOnUpdate, pictureFormat=args.pictureFormat,
                                             topicFilterRegex=topicFilterRegex, convertTimezone=convertTimezone, timeFormat=args.timeFormat,
                                             withRawJsonTopic=args.withRawJsonTopic, passive=False, updateOnConnect=False)

            mqttCLient.enable_logger()

            if usetls:
                if args.tls_version == "tlsv1.2":
                    tlsVersion = ssl.PROTOCOL_TLSv1_2
                elif args.tls_version == "tlsv1.1":
                    tlsVersion = ssl.PROTOCOL_TLSv1_1
                elif args.tls_version == "tlsv1":
                    tlsVersion = ssl.PROTOCOL_TLSv1
                elif args.tls_version is None:
                    tlsVersion = None
                else:
                    LOG.warning('Unknown TLS version %s - ignoring', args.tls_version)
                    tlsVersion = None

                if not args.insecure:
                    certRequired = ssl.CERT_REQUIRED
                else:
                    certRequired = ssl.CERT_NONE

                mqttCLient.tls_set(ca_certs=args.cacerts, certfile=args.cert, keyfile=args.key, cert_reqs=certRequired,
                                   tls_version=tlsVersion)
                if args.insecure:
                    mqttCLient.tls_insecure_set(True)

            if mqttusername is not None:
                mqttCLient.username_pw_set(username=mqttusername, password=mqttpassword)

            mqttCLient.connectWeConnect(weConnect)

            def mqttWorker():
                while True:
                    try:
                        mqttCLient.connect(args.mqttbroker, args.mqttport, args.mqttkeepalive)
                        break
                    except ConnectionRefusedError as e:
                        LOG.error('Could not connect to MQTT-Server: %s, will retry in 10 seconds', e)
                        time.sleep(10)
                # blocking run
                mqttCLient.loop_forever(retry_first_connection=True)
                mqttCLient.disconnect()
                LOG.error('MQTT Connection failed')

            mqttThread = threading.Thread(target=mqttWorker)
            mqttThread.start()

        ui = VWsFriendUI(weConnect=weConnect, connector=connector, homekitDriver=driver, dbUrl=args.dbUrl, configDir=args.configDir, username=username,
                         password=password)
        ui.run(host=args.host, port=args.port)

        if args.demo is not None:
            utcDemoStart = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
            # In demomode do not fix anything.
            weConnect.fixAPI = False
            for file in sorted(os.listdir(args.demo)):
                fileNameRegex = r'(?P<number>\d+)_(?P<delay>\d+)s(_(?P<stage>[^\.]+))?.cache.json'
                match = re.search(fileNameRegex, file)
                if match is not None:
                    time.sleep(int(match.groupdict()['delay']))
                    stageFilePath = f'{args.demo}/{file}'
                    with open(stageFilePath, mode='r', encoding='utf8') as fp:
                        cacheString = fp.read()
                        cacheString = re.sub(r'demodate\((?P<offset>[+-]?\d+)\)',
                                             lambda m: str(utcDemoStart + timedelta(seconds=int(m.groupdict()['offset']))).replace('+00:00', 'Z'), cacheString)
                        cacheString = re.sub(r'now\((?P<offset>[+-]?\d+)\)',
                                             lambda m: str(datetime.now() + timedelta(seconds=int(m.groupdict()['offset']))), cacheString)
                        weConnect.fillCacheFromJsonString(cacheString, maxAge=2147483647)
                        if args.withHomekit and not weConnectBridgeInitialized:
                            weConnectBridgeInitialized = True
                            bridge.update()
                        weConnect.update(updateCapabilities=True, updatePictures=False)
                        connector.commit()
                        if match.groupdict()['stage'] is not None:
                            LOG.info('Stage %s completed', match.groupdict()['stage'])
                        else:
                            LOG.info('Stage completed')
            LOG.info('Demo completed')
        else:
            starttime = time.time()
            subsequentErrors = 0
            permanentErrors = 0
            sleeptime = args.interval
            while True:
                try:
                    if SUPPORT_MQTT and args.mqttbroker:
                        mqttCLient.updateWeConnect(reraise=True)
                    else:
                        LOG.info('Updating data from WeConnect')
                        weConnect.update(updateCapabilities=True, updatePictures=True, force=True, selective=[Domain.ACCESS,
                                                                                                              Domain.ACTIVEVENTILATION,
                                                                                                              Domain.AUTOMATION,
                                                                                                              Domain.AUXILIARY_HEATING,
                                                                                                              Domain.USER_CAPABILITIES,
                                                                                                              Domain.CHARGING,
                                                                                                              Domain.CHARGING_PROFILES,
                                                                                                              Domain.BATTERY_CHARGING_CARE,
                                                                                                              Domain.CLIMATISATION,
                                                                                                              Domain.CLIMATISATION_TIMERS,
                                                                                                              Domain.DEPARTURE_TIMERS,
                                                                                                              Domain.FUEL_STATUS,
                                                                                                              Domain.VEHICLE_LIGHTS,
                                                                                                              Domain.LV_BATTERY,
                                                                                                              Domain.READINESS,
                                                                                                              Domain.VEHICLE_HEALTH_INSPECTION,
                                                                                                              Domain.VEHICLE_HEALTH_WARNINGS,
                                                                                                              Domain.OIL_LEVEL,
                                                                                                              Domain.MEASUREMENTS,
                                                                                                              Domain.BATTERY_SUPPORT,
                                                                                                              Domain.PARKING])
                    connector.commit()
                    if args.withHomekit and not weConnectBridgeInitialized:
                        weConnectBridgeInitialized = True
                        bridge.update()
                    sleeptime = args.interval - ((time.time() - starttime) % args.interval)
                    permanentErrors = 0
                    subsequentErrors = 0
                except weconnect.TooManyRequestsError:
                    if subsequentErrors > 0:
                        LOG.error('Retrieval error during update. Too many requests from your account. Will try again after 15 minutes')
                    else:
                        LOG.warning('Retrieval error during update. Too many requests from your account. Will try again after 15 minutes')
                    sleeptime = 900
                    subsequentErrors += 1
                except weconnect.RetrievalError:
                    if subsequentErrors > 0:
                        LOG.error('Retrieval error during update. Will try again after configured interval of %ds', args.interval)
                    else:
                        LOG.warning('Retrieval error during update. Will try again after configured interval of %ds', args.interval)
                    subsequentErrors += 1
                except TemporaryAuthentificationError:
                    if subsequentErrors > 0:
                        LOG.error('Temporary error during reauthentification. Will try again after configured interval of %ds', args.interval)
                    else:
                        LOG.warning('Temporary error during reauthentification. Will try again after configured interval of %ds', args.interval)
                    subsequentErrors += 1
                except APICompatibilityError as e:
                    sleeptime = min((args.interval * pow(2, permanentErrors)), 86400)
                    if subsequentErrors > 0:
                        LOG.critical('There was a problem when communicating with WeConnect. If this problem persists please open a bug report: %s,'
                                     ' will retry after %ds', e, sleeptime)
                    else:
                        LOG.warning('There was a problem when communicating with WeConnect. If this problem persists please open a bug report: %s,'
                                    ' will retry after %ds', e, sleeptime)
                    subsequentErrors += 1
                    permanentErrors += 1
                #  Execute exactly every interval but if it misses its deadline only after the next interval
                time.sleep(sleeptime)

    except AuthentificationError as e:
        LOG.critical('There was a problem when authenticating with WeConnect: %s', e)
    except APICompatibilityError as e:
        LOG.critical('There was a problem when communicating with WeConnect.'
                     ' If this problem persists please open a bug report: %s', e)
    finally:
        if weConnect is not None:
            weConnect.disconnect()
        if SUPPORT_MQTT and args.mqttbroker:
            if mqttCLient is not None:
                mqttCLient.disconnect()
