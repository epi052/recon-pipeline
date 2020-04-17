from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, Table, UniqueConstraint

from .base_model import Base


technology_association_table = Table(
    "technology_association",
    Base.metadata,
    Column("technology_id", Integer, ForeignKey("technology.id")),
    Column("target_id", Integer, ForeignKey("target.id")),
)


class Technology(Base):
    """ Database model that describes a web technology (i.e. Nginx 1.14).

        Represents webanalyze data.

        Relationships:
            ``targets``: many to many -> :class:`pipeline.models.target_model.Target`
    """

    __tablename__ = "technology"
    __table_args__ = (UniqueConstraint("type", "text"),)  # combination of type/text == unique

    def __str__(self):
        return self.pretty()

    def pretty(self, padlen=0):
        pad = "  "
        msg = f"{self.text} ({self.type})\n"
        msg += "=" * len(f"{self.text} ({self.type})")
        msg += "\n\n"

        for target in self.targets:
            if target.hostname:
                msg += f"{pad * padlen} - {target.hostname}\n"

            for ipaddr in target.ip_addresses:
                if ipaddr.ipv4_address:
                    msg += f"{pad * padlen} - {ipaddr.ipv4_address}\n"
                elif ipaddr.ipv6_address:
                    msg += f"{pad * padlen} - {ipaddr.ipv6_address}\n"

        return msg

    id = Column(Integer, primary_key=True)
    type = Column(String)
    text = Column(String)
    target_id = Column(Integer, ForeignKey("target.id"))
    targets = relationship("Target", secondary=technology_association_table, back_populates="technologies")
