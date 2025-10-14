import pytest

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
