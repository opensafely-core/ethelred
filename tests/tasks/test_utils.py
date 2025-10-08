import pytest

from tasks import io, utils


@pytest.mark.parametrize(
    "database, environment_variable",
    [
        (utils.Database.JOBSERVER, "JOBSERVER_DATABASE_URL"),
        (utils.Database.OPENCODELISTS, "OPENCODELISTS_DATABASE_URL"),
    ],
)
def test_get_engine(database, environment_variable, monkeypatch):
    monkeypatch.setenv(environment_variable, "sqlite+pysqlite:///:memory:")
    engine = utils.get_engine(database)
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


def test_hash_email():
    email = "user@example.com"
    hashed = utils.hash_email(email)
    assert hashed == "b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514"
