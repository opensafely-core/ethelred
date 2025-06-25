import pytest

from tasks import utils


def test_get_engine(monkeypatch):
    monkeypatch.setenv("JOBSERVER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    engine = utils.get_engine()
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


@pytest.mark.xfail
def test_get_metadata():
    assert False


@pytest.mark.xfail
def test_get_repo():
    assert False
