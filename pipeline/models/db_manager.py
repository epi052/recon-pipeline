import sqlite3
from pathlib import Path

from cmd2 import ansi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import *  # noqa: F403


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
        except sqlite3.IntegrityError as e:
            print(ansi.style(f"[!] exception during database transaction: {e}", fg="red"))
            self.session.rollback()

    def close(self):
        self.session.close()
