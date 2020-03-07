from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base
from .header_model import header_association_table


class Endpoint(Base):
    """ Database model that describes a URL/endpoint.

    Represents gobuster data.

    Relationships:
            ``target``: many to one -> :class:`models.target_model.Target`
            ``headers``: many to many -> :class:`models.header_model.Header`
    """

    __tablename__ = "endpoint"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    status_code = Column(Integer)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="endpoints")
    headers = relationship("Header", secondary=header_association_table, back_populates="endpoints")
