import datetime
import pathlib
from urllib.parse import urlparse

import pytest

from app import repositories


def test_repository_uris_have_valid_paths(tmp_path):
    repository = repositories.Repository(tmp_path.as_uri())
    for uri in repository.uris.values():
        path = urlparse(uri).path
        assert str(pathlib.Path(path)) == path


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
    events_csv.write_text("event_at\n2025-01-01 00:00:00\n2025-01-03 00:00:00")
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
