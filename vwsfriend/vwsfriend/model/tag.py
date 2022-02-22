from sqlalchemy import Column, String, Boolean

from vwsfriend.model.base import Base


class Tag(Base):
    __tablename__ = 'tag'
    name = Column(String, primary_key=True)
    description = Column(String, nullable=True)
    use_trips = Column(Boolean, default=False, nullable=False)
    use_charges = Column(Boolean, default=False, nullable=False)
    use_refueling = Column(Boolean, default=False, nullable=False)
    use_journey = Column(Boolean, default=False, nullable=False)

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
