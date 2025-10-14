import pytest

from app import repositories


@pytest.mark.xfail
def test_abstract_repository():
    class FakeRepository(repositories.AbstractRepository): ...

    with pytest.raises(TypeError):
        FakeRepository()


def test_repository(tmp_path):
    assert repositories.Repository(tmp_path)
