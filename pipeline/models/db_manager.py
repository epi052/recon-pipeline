import sqlite3
from pathlib import Path
from typing import Union

from cmd2 import ansi
from sqlalchemy import exc, or_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from .base_model import Base
from .target_model import Target
from .ip_address_model import IPAddress


class DBManager:
    def __init__(self, db_location):
        self.location = Path(db_location).resolve()
        engine = create_engine(f"sqlite:///{self.location}")
        Base.metadata.create_all(engine)  # noqa: F405
        session_factory = sessionmaker(bind=engine)
        self.session = session_factory()

    def add(self, item):
        try:
            self.session.add(item)
            self.session.commit()
        except (sqlite3.IntegrityError, exc.IntegrityError):
            print(ansi.style(f"[-] unique key constraint handled, moving on...", fg="bright_white"))
            self.session.rollback()

    def get_target_by_ip(self, ipaddr: str) -> Union[Target, None]:
        tgt = (
            self.session.query(Target)
            .filter(or_(IPAddress.ipv4_address == ipaddr, IPAddress.ipv6_address == ipaddr))
            .first()
        )
        return tgt

    def get_target_by_hostname(self, hostname: str) -> Target:
        return self.session.query(Target).filter(Target.hostname == hostname).first()

    def get_all_targets(self) -> list:
        return self.session.query(Target).all()

    def get_all_hostnames(self) -> list:
        return [x[0] for x in self.session.query(Target.hostname).filter(Target.hostname is not None)]

    def get_highest_id(self, table):
        highest = self.session.query(func.max(table.id)).first()[0]
        return highest if highest is not None else 1

    def close(self):
        self.session.close()
