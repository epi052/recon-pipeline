from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint, Table

from .base_model import Base

nse_result_association_table = Table(
    "nse_result_association",
    Base.metadata,
    Column("nse_result_id", Integer, ForeignKey("nse_result.id")),
    Column("nmap_result_id", Integer, ForeignKey("nmap_result.id")),
)


class NSEResult(Base):
    """ Database model that describes the NSE script executions as part of an nmap scan.

        Represents NSE script data.

        Relationships:
            ``NmapResult``: many to many -> :class:`models.nmap_model.NmapResult`
    """

    __tablename__ = "nse_result"
    __table_args__ = (UniqueConstraint("script_id", "script_output"),)  # combination of proto/port == unique

    id = Column(Integer, primary_key=True)
    script_id = Column(String)
    script_output = Column(String)

    nmap_result_id = Column(Integer, ForeignKey("nmap_result.id"))
    nmap_results = relationship("NmapResult", secondary=nse_result_association_table, back_populates="nse_results")
