import datetime

import pytest

from app import repositories


def test_abstract_repository():
    class FakeRepository(repositories.AbstractRepository): ...

    with pytest.raises(TypeError):
        FakeRepository()


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "opencodelists"
    path.mkdir()
    login_events_csv = path / "login_events.csv"
    login_events_csv.write_text(
        (
            "login_at,email_hash\n"
            + "2025-01-01 00:00:00,1111111\n"
            + "2025-01-03 00:00:00,3333333\n"
        )
    )
    codelist_create_events_csv = path / "codelist_create_events.csv"
    codelist_create_events_csv.write_text(
        ("created_at,id\n" + "2025-01-01 00:00:00,1\n" + "2025-01-03 00:00:00,3\n")
    )
    return repositories.Repository(tmp_path.as_uri())


def test_get_earliest_login_event_date(repository):
    assert repository.get_earliest_login_event_date() == datetime.date(2025, 1, 1)


def test_get_latest_login_event_date(repository):
    assert repository.get_latest_login_event_date() == datetime.date(2025, 1, 3)


@pytest.mark.filterwarnings(
    "ignore:The behavior of DatetimeProperties.to_pydatetime is deprecated:FutureWarning"
)
def test_get_events_per_day(repository):
    events_per_day = repositories._get_events_per_day(
        repository.login_events_uri,
        "login_at",
        datetime.date(2025, 1, 1),
        datetime.date(2025, 1, 3),
    )
    assert list(events_per_day["date"].dt.to_pydatetime()) == [
        datetime.datetime(2025, 1, 1),
        datetime.datetime(2025, 1, 2),  # not in fixture data
        datetime.datetime(2025, 1, 3),
    ]
    assert list(events_per_day["count"]) == [1, 0, 1]
