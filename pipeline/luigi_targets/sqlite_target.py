import luigi
from sqlalchemy.sql import exists

from ..models import DBManager


class SQLiteTarget(luigi.Target):
    """ Target to verify at least one row exists in a given table """

    def __init__(self, table, db_location, index=1):
        super().__init__()
        self.table = table
        self.index = index
        self.db_mgr = DBManager(db_location=db_location)

    # The exists method will be checked by luigi to ensure the Tasks that
    # output this target has been completed correctly
    def exists(self):
        result = self.db_mgr.session.query(self.table).filter(exists().where(self.table.id == f"{self.index}")).first()
        return result is not None
