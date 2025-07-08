import collections
import datetime

import sqlalchemy

from tasks import get_job_requests, io


Row = collections.namedtuple(
    "Row", ["url", "sha", "created_at", "num_jobs", "username"]
)


def test_get_query(
    jobserver_engine,
    jobserver_metadata,
    example_repo,
    example_workspace,
    example_user,
    make_jobrequest,
    make_job,
):
    # arrange
    repo_table = jobserver_metadata.tables["jobserver_repo"]
    insert_into_repo_table = sqlalchemy.insert(repo_table).values(example_repo)

    workspace_table = jobserver_metadata.tables["jobserver_workspace"]
    insert_into_workspace_table = sqlalchemy.insert(workspace_table).values(
        example_workspace
    )

    user_table = jobserver_metadata.tables["jobserver_user"]
    insert_into_user_table = sqlalchemy.insert(user_table).values(example_user)

    job_request_table = jobserver_metadata.tables["jobserver_jobrequest"]
    # before index date
    jobrequest_1 = make_jobrequest(
        id_=1,
        created_at=datetime.datetime(2024, 1, 1),
        workspace_id=example_workspace["id"],
        created_by_id=example_user["id"],
        sha="",
    )
    # on or after index date
    jobrequest_2 = make_jobrequest(
        id_=2,
        created_at=datetime.datetime(2025, 1, 1),
        workspace_id=example_workspace["id"],
        created_by_id=example_user["id"],
        sha="ABCDEFG",
    )
    insert_into_jobrequest_table = sqlalchemy.insert(job_request_table).values(
        [jobrequest_1, jobrequest_2]
    )

    job_table = jobserver_metadata.tables["jobserver_job"]
    jobs = [
        make_job(
            id_=123,
            job_request_id=1,
            created_at=datetime.datetime(2024, 1, 2),
        ),
        make_job(
            id_=456,
            job_request_id=2,
            created_at=datetime.datetime(2025, 1, 2),
        ),
        make_job(
            id_=789,
            job_request_id=2,
            created_at=datetime.datetime(2025, 1, 2),
        ),
    ]
    insert_into_job_table = sqlalchemy.insert(job_table).values(jobs)

    with jobserver_engine.connect() as conn:
        conn.execute(insert_into_repo_table)
        conn.execute(insert_into_workspace_table)
        conn.execute(insert_into_user_table)
        conn.execute(insert_into_jobrequest_table)
        conn.execute(insert_into_job_table)
        conn.commit()

    # act
    query = get_job_requests.get_query(jobserver_metadata)
    rows = get_job_requests.extract(jobserver_engine, query)
    rows = list(rows)

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row.url == "https://github.com/opensafely/my-repo"
    assert row.sha == "ABCDEFG"
    assert row.created_at == datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    assert row.num_jobs == 2
    assert row.username == "my-username"


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
