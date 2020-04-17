import textwrap
from pathlib import Path

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from .base_model import Base


class SearchsploitResult(Base):
    """ Database model that describes results from running searchsploit --nmap TARGET.xml.

        Represents searchsploit data.

        Relationships:
            ``target``: many to one -> :class:`pipeline.models.target_model.Target`
    """

    __tablename__ = "searchsploit_result"

    def __str__(self):
        return self.pretty()

    def pretty(self, fullpath=False):
        pad = "  "
        type_padlen = 8
        filename_padlen = 9

        if not fullpath:
            filename = Path(self.path).name

            msg = f"{pad}{self.type:<{type_padlen}} | {filename:<{filename_padlen}}"

            for i, line in enumerate(textwrap.wrap(self.title)):
                if i > 0:
                    msg += f"{' ' * (type_padlen + filename_padlen + 5)}|{pad * 2}{line}\n"
                else:
                    msg += f"|{pad}{line}\n"

            msg = msg[:-1]  # remove last newline
        else:
            msg = f"{pad}{self.type:<{type_padlen}}"

            for i, line in enumerate(textwrap.wrap(self.title)):
                if i > 0:
                    msg += f"{' ' * (type_padlen + 2)}|{pad * 2}{line}\n"
                else:
                    msg += f"|{pad}{line}\n"

            msg += f"{' ' * (type_padlen + 2)}|{pad}{self.path}"

        return msg

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    path = Column(String)
    type = Column(String)
    target_id = Column(Integer, ForeignKey("target.id"))
    target = relationship("Target", back_populates="searchsploit_results")
