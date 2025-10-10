from tasks import io, utils


def test_get_repo():
    repo = utils.get_repo("https://github.com/opensafely/my-repo")
    assert repo == "my-repo"


def test_load_project_definition(tmp_path):
    io.write({}, tmp_path / "my-repo" / "0000000.pickle")
    project_definition = utils.load_project_definition(tmp_path, "my-repo", "0000000")
    assert project_definition == {}


def test_sha256():
    hashed = utils.sha256("user@example.com")
    assert hashed == "b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514"
