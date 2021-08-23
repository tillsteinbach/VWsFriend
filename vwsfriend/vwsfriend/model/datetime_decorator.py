from datetime import datetime, timezone
import sqlalchemy


class DatetimeDecorator(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.DateTime
    cache_ok = True

    LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo

    def process_bind_param(self, value: datetime, dialect):
        if value is None:
            return value

        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)

        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)
