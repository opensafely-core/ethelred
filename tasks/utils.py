import datetime
import json
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


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return datetime.datetime.isoformat(obj)
        except TypeError:
            pass
        return super().default(obj)
