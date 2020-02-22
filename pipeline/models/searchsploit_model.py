from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base


class SearchsploitResult(Base):
    """ Database model that describes results from running searchsploit --nmap TARGET.xml.

        Represents searchsploit data.

        Relationships:
            ``target``: many to one -> :class:`models.target_model.Target`
    """

    __tablename__ = "searchsploit_result"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="searchsploit_results")
