import enum
import os

import sqlalchemy


class Database(enum.StrEnum):
    ETHELRED = enum.auto()
    JOBSERVER = enum.auto()
    OPENCODELISTS = enum.auto()


def get_engine(database):
    match database:
        case Database.ETHELRED:
            return sqlalchemy.create_engine(os.environ["ETHELRED_DATABASE_URL"])
        case Database.JOBSERVER:
            return sqlalchemy.create_engine(os.environ["JOBSERVER_DATABASE_URL"])
        case Database.OPENCODELISTS:
            return sqlalchemy.create_engine(os.environ["OPENCODELISTS_DATABASE_URL"])
        case _:
            raise TypeError(f"Cannot get engine for unknown database: {database}")


def get_metadata(engine):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=engine)
    return metadata
