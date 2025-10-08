import pytest

from tasks import io, utils


def test_get_engine(monkeypatch):
    monkeypatch.setenv("JOBSERVER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = utils.get_engine(utils.Database.JOBSERVER)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_engine_when_unknown_database():
    with pytest.raises(TypeError, match="Cannot get engine for unknown database: foo"):
        utils.get_engine("foo")


def test_get_metadata(monkeypatch):
    monkeypatch.setenv("JOBSERVER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    metadata = utils.get_metadata(utils.get_engine(utils.Database.JOBSERVER))
    assert metadata.tables == {}


def test_get_repo():
    repo = utils.get_repo("https://github.com/opensafely/my-repo")
    assert repo == "my-repo"


def test_load_project_definition(tmp_path):
    io.write({}, tmp_path / "my-repo" / "0000000.pickle")
    project_definition = utils.load_project_definition(tmp_path, "my-repo", "0000000")
    assert project_definition == {}
