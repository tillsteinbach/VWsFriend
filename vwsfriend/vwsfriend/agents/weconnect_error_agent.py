from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.exc import IntegrityError

from vwsfriend.model.weconnect_error import WeConnectError
from vwsfriend.model.weconnect_responsetime import WeConnectResponsetime

from weconnect.weconnect import WeConnect
from weconnect.weconnect_errors import ErrorEventType

LOG = logging.getLogger("VWsFriend")


class WeconnectErrorAgent():
    def __init__(self, session, weconnect: WeConnect):
        self.session = session
        self.weconnect = weconnect

        # register for updates:
        weconnect.addErrorObserver(self.__onError, ErrorEventType.ALL)

    def __onError(self, element, errortype, detail, message):
        error = WeConnectError(datetime.utcnow().replace(tzinfo=timezone.utc), errortype, detail)
        with self.session.begin_nested():
            try:
                self.session.add(error)
            except IntegrityError:
                LOG.warning('Could not add error entry to the database')
        self.session.commit()

    def commit(self):
        min = self.weconnect.getMinElapsed()
        if min is not None:
            min /= timedelta(microseconds=1)
        avg = self.weconnect.getAvgElapsed()
        if avg is not None:
            avg /= timedelta(microseconds=1)
        max = self.weconnect.getMaxElapsed()
        if max is not None:
            max /= timedelta(microseconds=1)
        total = self.weconnect.getTotalElapsed()
        if total is not None:
            total /= timedelta(microseconds=1)
        responsetime = WeConnectResponsetime(datetime.utcnow().replace(tzinfo=timezone.utc), min, avg, max, total)
        with self.session.begin_nested():
            try:
                self.session.add(responsetime)
            except IntegrityError:
                LOG.warning('Could not add responsetime entry to the database')
        self.session.commit()
