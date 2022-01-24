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
import getpass

import threading

from pyhap.accessory_driver import AccessoryDriver

from weconnect import weconnect
from weconnect.util import DuplicateFilter
from weconnect.__version import __version__ as __weconnect_version__

from vwsfriend.ui.vwsfriend_ui import VWsFriendUI
from vwsfriend.homekit.bridge import VWsFriendBridge
from vwsfriend.agent_connector import AgentConnector
from vwsfriend.privacy import Privacy

from vwsfriend.homekit.custom_characteristics import CUSTOM_CHARACTERISTICS

from .__version import __version__


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
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__} (using WeConnect-python {__weconnect_version__})')
    weConnectGroup = parser.add_argument_group('WeConnect')
    weConnectGroup.add_argument('-u', '--username', help='Username of Volkswagen id', required=False)
    weConnectGroup.add_argument('-p', '--password', help='Password of Volkswagen id', required=False)
    defaultNetRc = os.path.join(os.path.expanduser("~"), ".netrc")
    weConnectGroup.add_argument('--netrc', help=f'File in netrc syntax providing login (default: {defaultNetRc}).'
                                ' Netrc is only used when username and password are not provided  as arguments',
                                default=None, required=False)
    weConnectGroup.add_argument('-i', '--interval', help='Query interval in seconds',
                                type=NumberRangeArgument(imin=180), required=False, default=300)
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

    args = parser.parse_args()

    logLevel = LOG_LEVELS.index(DEFAULT_LOG_LEVEL)
    for adjustment in args.verbose or ():
        logLevel = min(len(LOG_LEVELS) - 1, max(logLevel + adjustment, 0))

    logging.basicConfig(level=LOG_LEVELS[logLevel], format=args.loggingFormat, datefmt=args.loggingDateFormat)
    logging.getLogger("pyhap").setLevel(level="CRITICAL")
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
            LOG.addHandler(smtpHandler)
            if args.loggingMailTestmail:
                msg = f'vwsfriend {__version__} (using WeConnect-python {__weconnect_version__})'
                smtpHandler.emit(logging.LogRecord('VWsFriend', logging.INFO, pathname=None, lineno=None, msg=msg, args=None, exc_info=None))
            smtpHandler.setLevel(logging.ERROR)
        else:
            LOG.error('You need to provide all --logging-mail options to make mail work')
            sys.exit(1)

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
            username, _, password = secrets.authenticators("volkswagen.de")
        except TypeError:
            if not args.username:
                LOG.error('volkswagen.de entry was not found in %s netrc-file. Create it or provide at least a username'
                          ' with --username', netRcFilename)
                sys.exit(1)
            username = args.username
            password = getpass.getpass()
        except FileNotFoundError:
            if not args.username:
                LOG.error('%s netrc-file was not found. Create it or provide at least a username with --username',
                          netRcFilename)
                sys.exit(1)
            username = args.username
            password = getpass.getpass()
    tokenfile = None
    if not args.noTokenStorage:
        tokenfile = args.tokenfile

    try:
        weConnect = weconnect.WeConnect(username=username, password=password, tokenfile=tokenfile,
                                        updateAfterLogin=False, loginOnInit=(args.demo is None), maxAgePictures=86400)

        connector = AgentConnector(weConnect=weConnect, dbUrl=args.dbUrl, interval=args.interval, withDB=args.withDatabase, withABRP=args.withABRP,
                                   configDir=args.configDir, privacy=args.privacy)

        driver = None
        if args.withHomekit:
            LOG.info('Starting up Homekit')
            # Start the accessory on port 51826
            driver = AccessoryDriver(pincode=None, persist_file=f'{args.configDir}/accessory.state')

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

        ui = VWsFriendUI(weConnect=weConnect, connector=connector, homekitDriver=driver, dbUrl=args.dbUrl, configDir=args.configDir)
        ui.run()

        if args.demo is not None:
            utcDemoStart = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
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
                        weConnect.update(updateCapabilities=True)
                        connector.commit()
                        if match.groupdict()['stage'] is not None:
                            LOG.info('Stage %s completed', match.groupdict()['stage'])
                        else:
                            LOG.info('Stage completed')
            LOG.info('Demo completed')
        else:
            starttime = time.time()
            while True:
                try:
                    LOG.info('Updating data from WeConnect')
                    weConnect.update(updateCapabilities=True, updatePictures=True, force=True)
                    connector.commit()
                    if args.withHomekit and not weConnectBridgeInitialized:
                        weConnectBridgeInitialized = True
                        bridge.update()
                except weconnect.RetrievalError:
                    LOG.error('Retrieval error during update. Will try again after configured interval of %ds', args.interval)
                #  Execute exactly every interval but if it misses its deadline only after the next interval
                time.sleep(args.interval - ((time.time() - starttime) % args.interval))

    except weconnect.AuthentificationError as e:
        LOG.critical('There was a problem when authenticating with WeConnect: %s', e)
    except weconnect.APICompatibilityError as e:
        LOG.critical('There was a problem when communicating with WeConnect.'
                     ' If this problem persists please open a bug report: %s', e)
    finally:
        weConnect.disconnect()
