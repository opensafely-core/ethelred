import enum
import os

import sqlalchemy

from . import io


class Database(enum.StrEnum):
    JOBSERVER = enum.auto()


def get_engine(database):
    match database:
        case Database.JOBSERVER:
            return sqlalchemy.create_engine(os.environ["JOBSERVER_DATABASE_URL"])
        case _:
            raise TypeError(f"Cannot get engine for unknown database: {database}")


def get_metadata(engine):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=engine)
    return metadata


def get_repo(url):
    return url.split("/")[-1]


def load_project_definition(project_definitions_dir, repo, sha):
    return io.read(project_definitions_dir / repo / f"{sha}.pickle")
