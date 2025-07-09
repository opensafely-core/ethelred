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
    assert record.stage == get_jobs.Stage.ANALYSIS.value
    assert record.outcome == get_jobs.Outcome.OTHER.value


@pytest.mark.parametrize(
    "run_command,stage",
    [
        ("ehrql:latest", get_jobs.Stage.DATABASE),
        ("ehrql:v1", get_jobs.Stage.DATABASE),
        ("python:v1", get_jobs.Stage.ANALYSIS),
        ("r:latest", get_jobs.Stage.ANALYSIS),
    ],
)
def test_get_stage(run_command, stage):
    assert get_jobs.get_stage(run_command) == stage.value


@pytest.mark.parametrize(
    "status, status_message, outcome",
    [
        ("failed", "Job exited with an error", get_jobs.Outcome.ERRORED),
        ("failed", "Job exited with an error: ...", get_jobs.Outcome.ERRORED),
        ("failed", "Internal error: this usually means...", get_jobs.Outcome.ERRORED),
        ("failed", "No outputs found matching patterns: ...", get_jobs.Outcome.ERRORED),
        (
            "failed",
            "GitRepoNotReachableError: Could not read ...",
            get_jobs.Outcome.ERRORED,
        ),
        (
            "failed",
            "Not starting as dependency failed",
            get_jobs.Outcome.CANCELLED_BY_DEPENDENCY,
        ),
        ("failed", "Cancelled by user", get_jobs.Outcome.OTHER),
        (
            "failed",
            "GithubValidationError: Branch name must not contain slashes ...",
            get_jobs.Outcome.OTHER,
        ),
        ("succeeded", "Completed successfully", get_jobs.Outcome.OTHER),
        ("running", "Job executing on the backend", get_jobs.Outcome.OTHER),
        ("pending", "Waiting on dependencies", get_jobs.Outcome.OTHER),
        ("pending", "Waiting on available workers", get_jobs.Outcome.OTHER),
    ],
)
def test_get_outcome(status, status_message, outcome):
    assert get_jobs.get_outcome(status, status_message) == outcome.value
