import collections
import datetime

import pytest

from tasks import get_jobs


Row = collections.namedtuple(
    "Row", ["id", "job_request_id", "created_at", "run_command"]
)


def test_transform():
    rows = [Row(123, 4567, datetime.datetime(2025, 1, 1), "python:v2 foo.py")]
    records = list(get_jobs.transform(rows))
    record = records[0]

    assert record.id == 123
    assert record.job_request_id == 4567
    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.stage == "analysis"


@pytest.mark.parametrize(
    "run_command,stage",
    [
        ("ehrql:latest", "database"),
        ("ehrql:v1", "database"),
        ("python:v1", "analysis"),
        ("r:latest", "analysis"),
    ],
)
def test_get_stage(run_command, stage):
    assert get_jobs.get_stage(run_command) == stage
