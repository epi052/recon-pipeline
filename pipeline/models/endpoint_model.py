from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base


class Endpoint(Base):
    """ Database model that describes a URL/endpoint.

    Represents gobuster data.

    Relationships:
            ``target``: many to one -> :class:`models.target_model.Target`
    """

    __tablename__ = "endpoint"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    status_code = Column(Integer)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="endpoints")
