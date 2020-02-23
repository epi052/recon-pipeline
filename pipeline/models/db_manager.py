from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import *


class DBManager:
    def __init__(self, db_location):
        self.location = Path(db_location).resolve()
        engine = create_engine(f"sqlite:///{self.location}")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        self.session = session_factory()

    def add(self, item):
        try:
            self.session.add(item)
            self.session.commit()
        except:
            self.session.rollback()

    def close(self):
        self.session.close()
