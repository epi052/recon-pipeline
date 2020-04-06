from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base


class IPAddress(Base):
    """ Database model that describes an ip address (ipv4 or ipv6).

        Represents amass data or targets specified manually as part of the ``target-file``.

        Relationships:
            ``target``: many to one -> :class:`pipeline.models.target_model.Target`
    """

    __tablename__ = "ip_address"

    id = Column(Integer, primary_key=True)
    ipv4_address = Column(String, unique=True)
    ipv6_address = Column(String, unique=True)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="ip_addresses")
