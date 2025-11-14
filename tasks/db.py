import enum
import os

import sqlalchemy


class Database(enum.StrEnum):
    OPENCODELISTS = enum.auto()


def get_engine(database):
    match database:
        case Database.OPENCODELISTS:
            return sqlalchemy.create_engine(
                "sqlite+pysqlite:///" + os.environ["OPENCODELISTS_DATABASE_PATH"]
            )
        case _:
            raise TypeError(f"Cannot get engine for database `{database}`")


def reflect_metadata(engine):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=engine)
    return metadata
