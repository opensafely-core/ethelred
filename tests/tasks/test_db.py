import pytest

from tasks import db


def test_get_engine(monkeypatch):
    monkeypatch.setenv("OPENCODELISTS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = db.get_engine(db.Database.OPENCODELISTS)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_engine_with_unknown_database():
    with pytest.raises(TypeError, match="Cannot get engine for unknown database: foo"):
        db.get_engine("foo")


def test_get_metadata(monkeypatch):
    monkeypatch.setenv("OPENCODELISTS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    metadata = db.get_metadata(db.get_engine(db.Database.OPENCODELISTS))
    assert metadata.tables == {}
