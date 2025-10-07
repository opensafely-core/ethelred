from tasks import io, utils


def test_get_engine():
    engine = utils.get_engine("sqlite+pysqlite:///:memory:")
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_metadata():
    metadata = utils.get_metadata(utils.get_engine("sqlite+pysqlite:///:memory:"))
    assert metadata.tables == {}


def test_get_repo():
    repo = utils.get_repo("https://github.com/opensafely/my-repo")
    assert repo == "my-repo"


def test_load_project_definition(tmp_path):
    io.write({}, tmp_path / "my-repo" / "0000000.pickle")
    project_definition = utils.load_project_definition(tmp_path, "my-repo", "0000000")
    assert project_definition == {}
