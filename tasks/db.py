import enum
import os

import sqlalchemy


class Database(enum.StrEnum):
    OPENCODELISTS = enum.auto()


def get_engine(database):
    match database:
        case Database.OPENCODELISTS:
            return sqlalchemy.create_engine(os.environ["OPENCODELISTS_DATABASE_URL"])
        case _:
            raise TypeError(f"Cannot get engine for unknown database: {database}")


def get_metadata(engine):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=engine)
    return metadata
