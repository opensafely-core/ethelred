import os

import sqlalchemy


def get_engine():
    return sqlalchemy.create_engine(os.environ["JOBSERVER_DATABASE_URL"])


def get_metadata(engine):
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=engine)
    return metadata


def get_repo(url):
    return url.split("/")[-1]
