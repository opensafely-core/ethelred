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
    job_1 = {
        "id": 1,
        "job_request_id": 1,
        "run_command": "my-command:v1",
        "status": "Succeeded",  # upper case
    }
    job_2 = {
        "id": 2,
        "job_request_id": 2,
        "run_command": "my-command:v1",
        "status": "Failed",  # upper case
    }
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
    assert row._fields == Row._fields
    assert row.id == 2
    assert row.status == "failed"  # lower case


def test_get_action():
    run_command = "ehrql:v1 generate-dataset analysis/dataset_definition.py"
    assert get_jobs.get_action(run_command) == ("ehrql", "v1")


@pytest.mark.parametrize(
    "action_name,action_type",
    [
        ("ehrql", "database"),
        ("cohortextractor", "database"),
        ("python", "analysis"),
        ("r", "analysis"),
        ("stata", "analysis"),
    ],
)
def test_get_action_type(action_name, action_type):
    assert get_jobs.get_action_type(action_name) == action_type


# We test against strings rather than StatusMessageType members to test that
# StatusMessageType is a subclass of StrEnum and so using auto results in
# lower-case member names as values.
@pytest.mark.parametrize(
    "status_message,status_message_type",
    [
        ("Not starting as dependency failed", "dependency_failed"),
        ("Not starting as no coffee", "other"),  # the wildcard case
        ("", "other"),  # the wildcard case, no status message
    ],
)
def test_get_status_message_type(status_message, status_message_type):
    assert get_jobs.get_status_message_type(status_message) == status_message_type


@pytest.mark.parametrize(
    "run_command,action_type",
    [
        ("ehrql:v1 generate-dataset analysis/dataset_definition.py", "database"),
        ("", ""),  # some jobs don't have run commands
    ],
)
def test_get_records(run_command, action_type):
    row = Row(
        id=1,
        job_request_id=2,
        created_at=datetime.datetime(2025, 1, 1),
        run_command=run_command,
        status="succeeded",
        status_message="Completed successfully",
    )

    records = list(get_jobs.get_records([row]))
    record = records[0]

    assert record.id == 1
    assert record.job_request_id == 2
    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.action_type == action_type
    assert record.status == "succeeded"
    assert record.status_message_type == "other"
