from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean

from .base_model import Base
from .port_model import port_association_table
from .technology_model import technology_association_table


class Target(Base):
    """ Database model that describes a target.

    This is the model that functions as the "top" model.

    Relationships:
        ``ip_addresses``: one to many -> :class:`models.ip_address_model.IPAddress`

        ``open_ports``: many to many -> :class:`models.port_model.Port`

        ``nmap_results``: one to many -> :class:`models.nmap_model.NmapResult`

        ``searchsploit_results``: one to many -> :class:`models.searchsploit_model.SearchsploitResult`

        ``endpoints``: one to many -> :class:`models.endpoint_model.Endpoint`

        ``technologies``: many to many -> :class:`models.technology_model.Technology`

        ``screenshots``: one to many -> :class:`models.screenshot_model.Screenshot`
    """

    __tablename__ = "target"

    id = Column(Integer, primary_key=True)
    headers = Column(String)
    hostname = Column(String, unique=True)
    is_web = Column(Boolean, default=False)
    vuln_to_sub_takeover = Column(Boolean, default=False)

    endpoints = relationship("Endpoint", back_populates="target")
    ip_addresses = relationship("IPAddress", back_populates="target")
    screenshots = relationship("Screenshot", back_populates="target")
    nmap_results = relationship("NmapResult", back_populates="target")
    searchsploit_results = relationship("SearchsploitResult", back_populates="target")
    open_ports = relationship("Port", secondary=port_association_table, back_populates="targets")
    technologies = relationship("Technology", secondary=technology_association_table, back_populates="targets")
