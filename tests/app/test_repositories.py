import datetime

import pytest
import sqlalchemy

from app import repositories


def test_abstract_repository():
    class FakeRepository(repositories.AbstractRepository): ...

    with pytest.raises(TypeError):
        FakeRepository()


@pytest.fixture
def repository(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path}/db.sqlite3"
    engine = sqlalchemy.create_engine(database_url)
    metadata = sqlalchemy.MetaData()
    logins_table = sqlalchemy.Table(
        "opencodelists_logins",
        metadata,
        sqlalchemy.Column("login_at", sqlalchemy.DateTime, primary_key=True),
        sqlalchemy.Column("email_hash", sqlalchemy.String(64), primary_key=True),
    )
    metadata.create_all(engine)
    with engine.connect() as conn:
        logins = [
            {"login_at": datetime.datetime(2025, 1, 1), "email_hash": 1111111},
            {"login_at": datetime.datetime(2025, 1, 3), "email_hash": 3333333},
        ]
        conn.execute(sqlalchemy.insert(logins_table), logins)
        conn.commit()
    return repositories.Repository(database_url)


def test_get_earliest_login_date(repository):
    assert repository.get_earliest_login_date() == datetime.datetime(2025, 1, 1)


def test_get_latest_login_date(repository):
    assert repository.get_latest_login_date() == datetime.datetime(2025, 1, 3)


def test_get_logins_per_day(repository):
    logins_per_day = repository.get_logins_per_day(
        datetime.date(2025, 1, 1), datetime.date(2025, 1, 3)
    )
    assert list(logins_per_day["date"].dt.to_pydatetime()) == [
        datetime.datetime(2025, 1, 1),
        datetime.datetime(2025, 1, 2),  # not in fixture data
        datetime.datetime(2025, 1, 3),
    ]
    assert list(logins_per_day["count"]) == [1, 0, 1]
