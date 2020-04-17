from sqlalchemy.orm import relationship, relation
from sqlalchemy import Column, Integer, ForeignKey, LargeBinary, Table, String

from .base_model import Base


screenshot_association_table = Table(
    "screenshot_association",
    Base.metadata,
    Column("screenshot_id", Integer, ForeignKey("screenshot.id")),
    Column("similar_page_id", Integer, ForeignKey("screenshot.id")),
)


class Screenshot(Base):
    """ Database model that describes a screenshot of a given webpage hosted on a ``Target``.

        Represents aquatone data.

        Relationships:
            ``port``: one to one -> :class:`pipeline.models.port_model.Port`

            ``target``: many to one -> :class:`pipeline.models.target_model.Target`

            ``endpoint``: one to one -> :class:`pipeline.models.endpoint_model.Endpoint`

            ``similar_pages``: black magic -> :class:`pipeline.models.screenshot_model.Screenshot`
    """

    __tablename__ = "screenshot"

    id = Column(Integer, primary_key=True)
    image = Column(LargeBinary)
    url = Column(String, unique=True)

    port = relationship("Port")
    port_id = Column(Integer, ForeignKey("port.id"))
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="screenshots")
    endpoint = relationship("Endpoint")
    endpoint_id = Column(Integer, ForeignKey("endpoint.id"))

    similar_pages = relation(
        "Screenshot",
        secondary=screenshot_association_table,
        primaryjoin=screenshot_association_table.c.screenshot_id == id,
        secondaryjoin=screenshot_association_table.c.similar_page_id == id,
        backref="similar_to",
    )
