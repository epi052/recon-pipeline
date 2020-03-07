import sqlite3
from pathlib import Path

from cmd2 import ansi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc, or_, create_engine
from sqlalchemy.sql.expression import func, ClauseElement

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

    def get_or_create(self, model, defaults=None, **kwargs):
        """ Simple helper to either get an existing record if it exists otherwise create and return a new instance """
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
            if defaults:
                params.update(defaults)
            instance = model(**params)
            return instance

    def add(self, item):
        """ Simple helper to add a record to the database """
        try:
            self.session.add(item)
            self.session.commit()
        except (sqlite3.IntegrityError, exc.IntegrityError):
            print(ansi.style(f"[-] unique key constraint handled, moving on...", fg="bright_white"))
            self.session.rollback()

    def get_target_by_ip_or_hostname(self, ip_or_host):
        """ Simple helper to query a Target record by either hostname or ip address, whichever works """
        return (
            self.session.query(Target)
            .filter(
                Target.ip_addresses.any(
                    or_(
                        IPAddress.ipv4_address.in_([ip_or_host]),
                        IPAddress.ipv6_address.in_([ip_or_host]),
                        Target.hostname == ip_or_host,
                    )
                )
            )
            .first()
        )

    def get_all_hostnames(self) -> list:
        """ Simple helper to return all hostnames from Target records """
        return [x[0] for x in self.session.query(Target.hostname).filter(Target.hostname is not None)]

    def get_highest_id(self, table):
        """ Simple helper to get the highest id number of the given table """
        highest = self.session.query(func.max(table.id)).first()[0]
        return highest if highest is not None else 1

    def close(self):
        """ Simple helper to close the database session """
        self.session.close()
