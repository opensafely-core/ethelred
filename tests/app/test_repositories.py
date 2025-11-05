import datetime
import pathlib
from urllib.parse import urlparse

import pandas
import pytest

from app import repositories


def test_repository_uris_have_valid_paths(tmp_path):
    repository = repositories.Repository(tmp_path.as_uri())
    for uri in repository.uris.values():
        path = urlparse(uri).path
        assert str(pathlib.Path(path)) == path


def test_get_num_users_logged_in_per_day(tmp_path):
    login_events_csv = tmp_path / "opencodelists" / "login_events.csv"
    login_events_csv.parent.mkdir()
    login_events_csv.write_text(
        "login_at,email_hash\n"
        + "2025-01-01 00:00:00,1111111\n"  # left boundary, should be counted
        + "2025-01-02 00:00:00,1111111\n"  # logged in twice, should be counted once
        + "2025-01-03 23:59:59,2222222\n"  # right boundary, should be counted
        + "2025-01-04 00:00:00,3333333\n"  # outside boundary, shouldn't be counted
    )
    repository = repositories.Repository(tmp_path.as_uri())
    from_ = datetime.date(2025, 1, 1)
    to_ = datetime.date(2025, 1, 3)
    obs = repository.get_num_users_logged_in_per_day(from_, to_)
    exp = pandas.DataFrame(
        {
            "date": [
                datetime.datetime(2025, 1, 1),
                datetime.datetime(2025, 1, 2),
                datetime.datetime(2025, 1, 3),
            ],
            "count": [1, 1, 2],
        }
    )
    pandas.testing.assert_frame_equal(obs, exp)


def test_repository_get_num_users_logged_in(tmp_path):
    login_events_csv = tmp_path / "opencodelists" / "login_events.csv"
    login_events_csv.parent.mkdir()
    login_events_csv.write_text(
        "login_at,email_hash\n"
        + "2025-01-01 00:00:00,1111111\n"  # left boundary, should be counted
        + "2025-01-02 00:00:00,1111111\n"  # logged in twice, shouldn't be counted
        + "2025-01-03 23:59:59,2222222\n"  # right boundary, should be counted
        + "2025-01-04 00:00:00,3333333\n"  # outside boundary, shouldn't be counted
    )
    repository = repositories.Repository(tmp_path.as_uri())
    from_ = datetime.date(2025, 1, 1)
    to_ = datetime.date(2025, 1, 3)
    assert repository.get_num_users_logged_in(from_, to_) == 2


def test_repository_get_num_codelists_created(tmp_path):
    events_csv = tmp_path / "opencodelists" / "codelist_create_events.csv"
    events_csv.parent.mkdir()
    events_csv.write_text(
        "created_at,id\n"
        + "2025-01-01 00:00:00,1\n"  # left boundary, should be counted
        + "2025-01-03 23:59:59,2\n"  # right boundary, should be counted
        + "2025-01-04 00:00:00,3\n"  # outside boundary, shouldn't be counted
    )
    repository = repositories.Repository(tmp_path.as_uri())
    from_ = datetime.date(2025, 1, 1)
    to_ = datetime.date(2025, 1, 3)
    assert repository.get_num_codelists_created(from_, to_) == 2


def test_get_scalar_result(tmp_path):
    my_csv = tmp_path / "my.csv"
    my_csv.write_text("val\n2\n3\n1")
    scalar_result = repositories._get_scalar_result(my_csv.as_uri(), "max", "val")
    assert scalar_result == 3


@pytest.mark.filterwarnings(
    "ignore:The behavior of DatetimeProperties.to_pydatetime is deprecated:FutureWarning"
)
def test_get_events_per_day(tmp_path):
    events_csv = tmp_path / "events.csv"
    events_csv.write_text(
        "event_at\n"
        + "2025-01-01 00:00:00\n"  # left boundary, should be counted
        + "2025-01-03 23:59:59\n"  # right boundary, should be counted
        + "2025-01-04 00:00:00\n"  # outside boundary, shouldn't be counted
    )
    events_per_day = repositories._get_events_per_day(
        events_csv.as_uri(),
        "event_at",
        datetime.date(2025, 1, 1),
        datetime.date(2025, 1, 3),
    )
    assert list(events_per_day["date"].dt.to_pydatetime()) == [
        datetime.datetime(2025, 1, 1),
        datetime.datetime(2025, 1, 2),  # not in fixture data
        datetime.datetime(2025, 1, 3),
    ]
    assert list(events_per_day["count"]) == [1, 0, 1]
