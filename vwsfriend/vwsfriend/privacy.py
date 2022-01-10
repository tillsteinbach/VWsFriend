from enum import Enum


class Privacy(Enum):
    NO_LOCATIONS = 'no-locations'

    def __str__(self):
        return self.value
