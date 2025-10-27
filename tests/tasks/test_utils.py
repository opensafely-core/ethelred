from tasks import utils


def test_sha256():
    hashed = utils.sha256("user@example.com")
    assert hashed == "b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514"
