from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint, Table

from .base_model import Base

header_association_table = Table(
    "header_association",
    Base.metadata,
    Column("header_id", Integer, ForeignKey("header.id")),
    Column("endpoint_id", Integer, ForeignKey("endpoint.id")),
)


class Header(Base):
    """ Database model that describes an http header (i.e. Server=cloudflare).

        Relationships:
            ``endpoints``: many to many -> :class:`pipeline.models.target_model.Endpoint`
    """

    __tablename__ = "header"
    __table_args__ = (UniqueConstraint("name", "value"),)  # combination of name/value == unique

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    endpoint_id = Column(Integer, ForeignKey("endpoint.id"))
    endpoints = relationship("Endpoint", secondary=header_association_table, back_populates="headers")
