import collections
import datetime

import pytest

from tasks import get_jobs


Row = collections.namedtuple(
    "Row",
    ["id", "job_request_id", "created_at", "run_command", "status", "status_message"],
)


def test_transform():
    rows = [
        Row(
            123,
            4567,
            datetime.datetime(2025, 1, 1),
            "python:v2 foo.py",
            "succeeded",
            "Completed successfully",
        )
    ]
    records = list(get_jobs.transform(rows))
    record = records[0]

    assert record.id == 123
    assert record.job_request_id == 4567
    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.stage == "analysis"
    assert record.outcome == "other"


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


@pytest.mark.parametrize(
    "status, status_message, outcome",
    [
        ("failed", "Job exited with an error", "errored"),
        ("failed", "Job exited with an error: ...", "errored"),
        ("failed", "Internal error: this usually means...", "errored"),
        ("failed", "No outputs found matching patterns: ...", "errored"),
        ("failed", "GitRepoNotReachableError: Could not read from...", "errored"),
        ("failed", "Not starting as dependency failed", "cancelled by dependency"),
        ("failed", "Cancelled by user", "other"),
        ("failed", "... Branch name must not contain slashes ...", "other"),
        ("succeeded", "Completed successfully", "other"),
        ("running", "Job executing on the backend", "other"),
        ("pending", "Waiting on dependencies", "other"),
        ("pending", "Waiting on available workers", "other"),
    ],
)
def test_get_outcome(status, status_message, outcome):
    assert get_jobs.get_outcome(status, status_message) == outcome
