import collections

import pytest
import sqlalchemy

from tasks import db


@pytest.mark.parametrize(
    "database, environment_variable",
    [
        (db.Database.JOBSERVER, "JOBSERVER_DATABASE_URL"),
        (db.Database.OPENCODELISTS, "OPENCODELISTS_DATABASE_URL"),
        (db.Database.ETHELRED, "ETHELRED_DATABASE_URL"),
    ],
)
def test_get_engine(database, environment_variable, monkeypatch):
    monkeypatch.setenv(environment_variable, "sqlite+pysqlite:///:memory:")
    engine = db.get_engine(database)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_engine_when_unknown_database():
    with pytest.raises(TypeError, match="Cannot get engine for unknown database: foo"):
        db.get_engine("foo")


def test_get_metadata(monkeypatch):
    monkeypatch.setenv("JOBSERVER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    metadata = db.get_metadata(db.get_engine(db.Database.JOBSERVER))
    assert metadata.tables == {}


def test_write_records():
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:")
    table = sqlalchemy.Table(
        "test", sqlalchemy.MetaData(), sqlalchemy.Column("col_1", sqlalchemy.String)
    )
    Record = collections.namedtuple("Record", ["col_1"])

    db.write_records([Record("value_1"), Record("value_2")], engine, table)

    with engine.connect() as conn:
        rows = list(conn.execute(sqlalchemy.select(table)))
    assert len(rows) == 2
    assert rows[0]._fields == Record._fields
    assert rows[0].col_1 == "value_1"


def test_write_records_overwrites_existing_table():
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:")
    table = sqlalchemy.Table(
        "test", sqlalchemy.MetaData(), sqlalchemy.Column("col_1", sqlalchemy.String)
    )
    Record = collections.namedtuple("Record", ["col_1"])
    table.create(engine)
    with engine.begin() as conn:
        conn.execute(sqlalchemy.insert(table), {"col_1": "old_value"})

    db.write_records([Record("new_value")], engine, table)

    with engine.connect() as conn:
        rows = list(conn.execute(sqlalchemy.select(table)))
    assert len(rows) == 1
    assert rows[0].col_1 == "new_value"
