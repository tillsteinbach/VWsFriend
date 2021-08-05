import os
import sys
import re
import argparse
from datetime import datetime, timedelta, timezone
import logging
import time
import tempfile
import netrc
import getpass

import threading

from pyhap.accessory_driver import AccessoryDriver

from weconnect import weconnect
from weconnect.__version import __version__ as __weconnect_version__
from vwsfriend.homekit.bridge import VWsFriendBridge
from vwsfriend.model.db_connector import DBConnector

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


def main():  # noqa: C901 pylint: disable=too-many-branches, too-many-statements
    parser = argparse.ArgumentParser(
        prog='vwsfriend',
        description='TBD')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version} (using WeConnect-python {weversion})'.format(version=__version__, weversion=__weconnect_version__))
    parser.add_argument('-u', '--username', help='Username of Volkswagen id', required=False)
    parser.add_argument('-p', '--password', help='Password of Volkswagen id', required=False)
    parser.add_argument('--database-url', dest='dbUrl', help='Database to connect to', default='sqlite:///vwsfrienddevel.db')
    defaultNetRc = os.path.join(os.path.expanduser("~"), ".netrc")
    parser.add_argument('--netrc', help=f'File in netrc syntax providing login (default: {defaultNetRc}).'
                        ' Netrc is only used when username and password are not provided  as arguments',
                        default=None, required=False)
    parser.add_argument('-v', '--verbose', action="append_const", const=-1,)
    parser.add_argument('--no-token-storage', dest='noTokenStorage', help='Do not store token on filesystem (this'
                        ' will cause a new login for every invokation!)', action='store_true')
    defaultTemp = os.path.join(tempfile.gettempdir(), 'weconnect.token')
    parser.add_argument('--tokenfile', help=f'file to store token (default: {defaultTemp})', default=defaultTemp)
    parser.add_argument('-i', '--interval', help='Query interval in seconds',
                              type=NumberRangeArgument(imin=300), required=False, default=300)
    parser.add_argument('--demo', help=f'folder containing demo scenario, see README for more information')

    args = parser.parse_args()

    logLevel = LOG_LEVELS.index(DEFAULT_LOG_LEVEL)
    for adjustment in args.verbose or ():
        logLevel = min(len(LOG_LEVELS) - 1, max(logLevel + adjustment, 0))

    logging.basicConfig(level=LOG_LEVELS[logLevel])
    logging.getLogger("pyhap").setLevel(level="CRITICAL")

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
                                        updateAfterLogin=False, loginOnInit=(args.demo is None))

        connector = DBConnector(weConnect=weConnect, dbUrl=args.dbUrl, interval=args.interval)

        if args.demo is not None:
            utcDemoStart = datetime.utcnow().replace(tzinfo=timezone.utc, microsecond=0)
            for file in sorted(os.listdir(args.demo)):
                fileNameRegex = r'(?P<number>\d+)_(?P<delay>\d+)s(_(?P<stage>[^\.]+))?.cache.json'
                match = re.search(fileNameRegex, file)
                if match is not None:
                    time.sleep(int(match.groupdict()['delay']))
                    stageFilePath = f'{args.demo}/{file}'
                    with open(stageFilePath,"r") as fp:
                        cacheString = fp.read()
                        cacheString =re.sub(r'demodate\((?P<offset>[+-]?\d+)\)', lambda m: str(utcDemoStart + timedelta(seconds=int(m.groupdict()['offset']))).replace('+00:00', 'Z'), cacheString)
                        cacheString =re.sub(r'now\((?P<offset>[+-]?\d+)\)', lambda m: str(datetime.now() + timedelta(seconds=int(m.groupdict()['offset']))), cacheString)
                        weConnect.fillCacheFromJsonString(cacheString, maxAge=2147483647)
                        weConnect.update(updateCapabilities=False)
                        connector.commit()
                        if match.groupdict()['stage'] is not None:
                            LOG.info('Stage %s completed', match.groupdict()['stage'])
                        else:
                            LOG.info('Stage completed')
            LOG.info('Demo completed')
        else:
            while True:
                try:
                    LOG.info('Updating data from WeConnect')
                    weConnect.update(updateCapabilities=False, updatePictures=False)
                    connector.commit()
                except weconnect.RetrievalError:
                    LOG.error('Retrieval error during update. Will try again after configured interval of %ds', args.interval)
                time.sleep(args.interval)

        sys.exit(0)
        # flake8: noqa

        # Start the accessory on port 51826
        driver = AccessoryDriver(pincode=b'123-45-678')
        bridge = VWsFriendBridge(driver=driver, weConnect=weConnect)
        driver.add_accessory(bridge)

        #  signal.signal(signal.SIGTERM, driver.signal_handler)

        # Start it!
        #driver.async_start()
        #driver.start()

        x = threading.Thread(target=driver.start,)
        x.start()
        toggle = True
        while True:
            if args.fromcache:
                time.sleep(10)
            else:
                time.sleep(600)
            toggle = not toggle
            if toggle:
                if args.fromcache:
                    weConnect.fillCacheFromJson(args.cachefile, maxAge=2147483647)
                weConnect.update(updateCapabilities=False)
            else:
                if args.fromcache:
                    weConnect.fillCacheFromJson(args.cachefile2, maxAge=2147483647)
                weConnect.update(updateCapabilities=False)

    except weconnect.AuthentificationError as e:
        LOG.critical('There was a problem when authenticating with WeConnect: %s', e)
    except weconnect.APICompatibilityError as e:
        LOG.critical('There was a problem when communicating with WeConnect.'
                     ' If this problem persists please open a bug report: %s', e)
