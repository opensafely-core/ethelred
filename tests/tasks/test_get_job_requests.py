import collections
import datetime

import sqlalchemy

from tasks import get_job_requests, io


Row = collections.namedtuple(
    "Row", ["url", "sha", "created_at", "num_jobs", "username"]
)


def test_extract(jobserver_engine, jobserver_metadata):
    # arrange
    a_foreign_key = 99

    repo_table = jobserver_metadata.tables["jobserver_repo"]
    repo_id = 1
    insert_into_repo_table = sqlalchemy.insert(repo_table).values(
        id=repo_id,
        url="https://github.com/opensafely/my-repo",
        has_github_outputs=False,
    )

    workspace_table = jobserver_metadata.tables["jobserver_workspace"]
    workspace_id = 1
    insert_into_workspace_table = sqlalchemy.insert(workspace_table).values(
        id=workspace_id,
        created_by_id=a_foreign_key,
        project_id=a_foreign_key,
        uses_new_release_flow=True,
        repo_id=repo_id,
        signed_off_by_id=a_foreign_key,
        purpose="a purpose",
        updated_at=datetime.datetime(2025, 1, 1),
        updated_by_id=a_foreign_key,
    )

    user_table = jobserver_metadata.tables["jobserver_user"]
    user_id = 1
    insert_into_user_table = sqlalchemy.insert(user_table).values(
        id=user_id, username="a_user", fullname="a user", roles=[]
    )

    jobrequest_table = jobserver_metadata.tables["jobserver_jobrequest"]
    template_jobrequest = {
        "id": None,  # replace me
        "sha": None,  # replace me
        "created_at": None,  # replace me
        "backend_id": a_foreign_key,
        "created_by_id": user_id,
        "workspace_id": workspace_id,
        "requested_actions": ["a1"],
        "project_definition": "actions: {a1: {}, a2: {}}",
        "codelists_ok": True,
    }
    # before index date
    jobrequest_1 = template_jobrequest | {
        "id": 1,
        "sha": "1111111",
        "created_at": datetime.datetime(2024, 1, 1),
    }
    # on or after index date
    jobrequest_2 = template_jobrequest | {
        "id": 2,
        "sha": "2222222",
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
        conn.execute(insert_into_repo_table)
        conn.execute(insert_into_workspace_table)
        conn.execute(insert_into_user_table)
        conn.execute(insert_into_jobrequest_table)
        conn.execute(insert_into_job_table)
        conn.commit()

    # act
    rows = list(get_job_requests.extract(jobserver_engine, jobserver_metadata))

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row._fields == Row._fields
    assert row.sha == "2222222"
    assert row.num_jobs == 1


def test_load_project_definition(tmp_path):
    io.write({}, tmp_path / "my-repo" / "0000000.pickle")
    project_definition = get_job_requests.load_project_definition(
        tmp_path, "my-repo", "0000000"
    )
    assert project_definition == {}


def test_get_records():
    row = Row(
        "https://github.com/opensafely/my-repo",
        "0000000",
        datetime.datetime(2025, 1, 1),
        1,
        "my-username",
    )

    def load_project_definition(repo, sha):
        return {"actions": {"a1": {}, "a2": {}}}

    records = list(get_job_requests.get_records([row], load_project_definition))
    record = records[0]

    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.num_actions == 2
    assert record.num_jobs == 1
