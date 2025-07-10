import collections
import datetime

import pytest
import sqlalchemy

from tasks import get_jobs


Row = collections.namedtuple(
    "Row",
    ["id", "job_request_id", "created_at", "run_command", "status", "status_message"],
)


def test_extract(jobserver_engine, jobserver_metadata):
    # arrange
    a_foreign_key = 99

    jobrequest_table = jobserver_metadata.tables["jobserver_jobrequest"]
    template_jobrequest = {
        "id": None,  # replace me
        "sha": "0000000",
        "created_at": None,  # replace me
        "backend_id": a_foreign_key,
        "created_by_id": a_foreign_key,
        "workspace_id": a_foreign_key,
        "requested_actions": ["a1"],
        "project_definition": "actions: {a1: {}, a2: {}}",
        "codelists_ok": True,
    }
    # before index date
    jobrequest_1 = template_jobrequest | {
        "id": 1,
        "created_at": datetime.datetime(2024, 1, 1),
    }
    # on or after index date
    jobrequest_2 = template_jobrequest | {
        "id": 2,
        "created_at": datetime.datetime(2025, 1, 1),
    }
    insert_into_jobrequest_table = sqlalchemy.insert(jobrequest_table).values(
        [jobrequest_1, jobrequest_2]
    )

    job_table = jobserver_metadata.tables["jobserver_job"]
    job_1 = {"id": 1, "job_request_id": 1, "run_command": "my-command:v1"}
    job_2 = {"id": 2, "job_request_id": 2, "run_command": "my-command:v1"}
    insert_into_job_table = sqlalchemy.insert(job_table).values([job_1, job_2])

    with jobserver_engine.connect() as conn:
        conn.execute(insert_into_jobrequest_table)
        conn.execute(insert_into_job_table)
        conn.commit()

    # act
    rows = list(get_jobs.extract(jobserver_engine, jobserver_metadata))

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row._fields == (
        "id",
        "job_request_id",
        "created_at",
        "run_command",
        "status",
        "status_message",
    )
    assert row.id == 2


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
        ("ehrql:v1", "database"),
        ("python:v1", "analysis"),
        ("r:v1", "analysis"),
        ("stata:latest", "analysis"),
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
