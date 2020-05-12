import textwrap

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean

from .base_model import Base
from .port_model import Port
from .ip_address_model import IPAddress
from .nse_model import nse_result_association_table


class NmapResult(Base):
    """ Database model that describes the TARGET.nmap scan results.

        Represents nmap data.

        Relationships:
            ``target``: many to one -> :class:`pipeline.models.target_model.Target`

            ``ip_address``: one to one -> :class:`pipeline.models.ip_address_model.IPAddress`

            ``port``: one to one -> :class:`pipeline.models.port_model.Port`

            ``nse_results``: one to many -> :class:`pipeline.models.nse_model.NSEResult`
    """

    def __str__(self):
        return self.pretty()

    def pretty(self, commandline=False, nse_results=None):
        pad = "  "

        ip_address = self.ip_address.ipv4_address or self.ip_address.ipv6_address

        msg = f"{ip_address} - {self.service}\n"
        msg += f"{'=' * (len(ip_address) + len(self.service) + 3)}\n\n"
        msg += f"{self.port.protocol} port: {self.port.port_number} - {'open' if self.open else 'closed'} - {self.reason}\n"
        msg += f"product: {self.product} :: {self.product_version}\n"
        msg += "nse script(s) output:\n"

        if nse_results is None:
            # add all nse scripts
            for nse_result in self.nse_results:
                msg += f"{pad}{nse_result.script_id}\n"
                msg += textwrap.indent(nse_result.script_output, pad * 2)
                msg += "\n"
        else:
            # filter used, only return those specified
            for nse_result in nse_results:
                if nse_result in self.nse_results:
                    msg += f"{pad}{nse_result.script_id}\n"
                    msg += textwrap.indent(nse_result.script_output, pad * 2)
                    msg += "\n"

        if commandline:
            msg += "command used:\n"
            msg += f"{pad}{self.commandline}\n"

        return msg

    __tablename__ = "nmap_result"

    id = Column(Integer, primary_key=True)
    open = Column(Boolean)
    reason = Column(String)
    service = Column(String)
    product = Column(String)
    commandline = Column(String)
    product_version = Column(String)

    port = relationship(Port)
    port_id = Column(Integer, ForeignKey("port.id"))
    ip_address = relationship(IPAddress)
    ip_address_id = Column(Integer, ForeignKey("ip_address.id"))
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="nmap_results")
    nse_results = relationship("NSEResult", secondary=nse_result_association_table, back_populates="nmap_results")
