from datetime import datetime, timezone
import logging
from sqlalchemy.exc import IntegrityError

from vwsfriend.model.weconnect_error import WeConnectError

from weconnect.weconnect import WeConnect

LOG = logging.getLogger("VWsFriend")


class WeconnectErrorAgent():
    def __init__(self, session, weconnect: WeConnect):
        self.session = session
        self.weconnect = weconnect

        # register for updates:
        weconnect.addErrorObserver(self.__onError, WeConnect.ErrorEventType.ALL)

    def __onError(self, element, errortype, detail, message):
        error = WeConnectError(datetime.utcnow().replace(tzinfo=timezone.utc), errortype, detail)
        try:
            with self.session.begin_nested():
                self.session.add(error)
            self.session.commit()
        except IntegrityError:
            LOG.warning('Could not add error entry to the database, this is usually due to an error in the WeConnect API')

    def commit(self):
        pass
