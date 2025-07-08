import collections
import datetime

import pytest
import sqlalchemy

from tasks import get_jobs


Row = collections.namedtuple(
    "Row",
    ["id", "job_request_id", "created_at", "run_command", "status", "status_message"],
)


@pytest.fixture
def make_job():
    def _make_job(id_, job_request_id, created_at):
        return {
            "id": id_,
            "job_request_id": job_request_id,
            "created_at": created_at,
            "action": "do_something",
            "run_command": "command:version some_script.py",
            "status": "some status",
            "status_code": "000",
            "status_message": "some status message",
        }

    return _make_job


def test_get_query(jobserver_engine, jobserver_metadata, make_job, make_jobrequest):
    # arrange
    job_request_table = jobserver_metadata.tables["jobserver_jobrequest"]
    # before index date
    jobrequest_1 = make_jobrequest(
        id_=1,
        created_at=datetime.datetime(2024, 1, 1),
    )
    # on or after index date
    jobrequest_2 = make_jobrequest(
        id_=2,
        created_at=datetime.datetime(2025, 1, 1),
    )
    insert_into_jobrequest_table = sqlalchemy.insert(job_request_table).values(
        [jobrequest_1, jobrequest_2]
    )

    job_table = jobserver_metadata.tables["jobserver_job"]
    job_1 = make_job(
        id_=123,
        job_request_id=1,
        created_at=datetime.datetime(2024, 1, 1),
    )
    job_2 = make_job(
        id_=456,
        job_request_id=2,
        created_at=datetime.datetime(2025, 1, 2),
    )
    insert_into_job_table = sqlalchemy.insert(job_table).values([job_1, job_2])

    with jobserver_engine.connect() as conn:
        conn.execute(insert_into_jobrequest_table)
        conn.execute(insert_into_job_table)
        conn.commit()

    # act
    query = get_jobs.get_query(jobserver_metadata)
    rows = get_jobs.extract(jobserver_engine, query)
    rows = list(rows)

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row.id == 456
    assert row.job_request_id == 2
    assert row.created_at == datetime.datetime(2025, 1, 2, tzinfo=datetime.timezone.utc)
    assert row.run_command == "command:version some_script.py"
    assert row.status == "some status"
    assert row.status_message == "some status message"


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
