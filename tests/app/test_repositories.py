import datetime

import pytest

from app import repositories


def test_abstract_repository():
    class FakeRepository(repositories.AbstractRepository): ...

    with pytest.raises(TypeError):
        FakeRepository()


@pytest.fixture
def repository(tmp_path):
    logins_path = tmp_path / "opencodelists" / "login_events.csv"
    logins_path.parent.mkdir()
    logins_path.write_text(
        (
            "login_at,email_hash\n"
            + "2025-01-01 00:00:00,1111111\n"
            + "2025-01-03 00:00:00,3333333\n"
        )
    )
    return repositories.Repository(tmp_path.as_uri())


def test_get_earliest_login_date(repository):
    assert repository.get_earliest_login_date() == datetime.date(2025, 1, 1)


def test_get_latest_login_date(repository):
    assert repository.get_latest_login_date() == datetime.date(2025, 1, 3)


@pytest.mark.filterwarnings(
    "ignore:The behavior of DatetimeProperties.to_pydatetime is deprecated:FutureWarning"
)
def test_get_logins_per_day(repository):
    logins_per_day = repository.get_logins_per_day(
        datetime.date(2025, 1, 1), datetime.date(2025, 1, 3)
    )
    assert list(logins_per_day["date"].dt.to_pydatetime()) == [
        datetime.datetime(2025, 1, 1),
        datetime.datetime(2025, 1, 2),  # not in fixture data
        datetime.datetime(2025, 1, 3),
    ]
    assert list(logins_per_day["count"]) == [1, 0, 1]
