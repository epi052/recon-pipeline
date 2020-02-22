from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, VARBINARY

from .base_model import Base


class Screenshot(Base):
    """ Database model that describes a screenshot of a given webpage hosted on a ``Target``.

        Represents aquatone data.

        Relationships:
            ``port``: one to one -> :class:`models.port_model.Port`
            ``target``: many to one -> :class:`models.target_model.Target`
    """

    __tablename__ = "screenshot"

    id = Column(Integer, primary_key=True)
    image = VARBINARY()
    port = relationship("Port")
    port_id = Column(Integer, ForeignKey("port.id"))
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="screenshots")
