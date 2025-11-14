import pytest
import sqlalchemy

from tasks import db


def test_get_engine(monkeypatch):
    monkeypatch.setenv("OPENCODELISTS_DATABASE_PATH", ":memory:")
    engine = db.get_engine(db.Database.OPENCODELISTS)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_engine_with_unknown_database():
    with pytest.raises(TypeError, match="Cannot get engine for database `foo`"):
        db.get_engine("foo")


def test_reflect_metadata():
    engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:")
    with engine.connect() as conn:
        sqlalchemy.Table(
            "my_table",
            sqlalchemy.MetaData(),
            sqlalchemy.Column("my_column", sqlalchemy.String),
        ).create(conn)

    metadata = db.reflect_metadata(engine)
    assert "my_table" in metadata.tables
