from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base


class NmapResult(Base):
    """ Database model that describes the TARGET.nmap scan results.

        Represents nmap data.

        Relationships:
            ``target``: many to one -> :class:`models.target_model.Target`
    """

    __tablename__ = "nmap_result"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="nmap_results")
