import collections
import datetime

import sqlalchemy

from tasks import get_project_definitions, io


Row = collections.namedtuple("Row", ["url", "sha", "project_definition"])


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

    jobrequest_table = jobserver_metadata.tables["jobserver_jobrequest"]
    template_jobrequest = {
        "id": None,  # replace me
        "sha": None,  # replace me
        "created_at": None,  # replace me
        "backend_id": a_foreign_key,
        "created_by_id": a_foreign_key,
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

    with jobserver_engine.connect() as conn:
        conn.execute(insert_into_repo_table)
        conn.execute(insert_into_workspace_table)
        conn.execute(insert_into_jobrequest_table)
        conn.commit()

    # act
    rows = list(get_project_definitions.extract(jobserver_engine, jobserver_metadata))

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row._fields == ("url", "sha", "project_definition")
    assert row.sha == "2222222"


def test_get_record():
    row = Row(
        "https://github.com/opensafely/my-repo",
        "0000000",
        """
        actions:
            a1: {}
            a2: {}
        """,
    )
    record = get_project_definitions.get_record(row)
    assert record.repo == "my-repo"
    assert record.sha == "0000000"
    assert record.project_definition == {"actions": {"a1": {}, "a2": {}}}


def test_write_pickle(tmp_path):
    record = get_project_definitions.Record(
        "my-repo", "0000000", {"actions": {"a1": {}, "a2": {}}}
    )
    project_definitions_dir = tmp_path / "project_definitions"

    get_project_definitions.write_pickle([record], project_definitions_dir)

    project_definition = io.read(project_definitions_dir / "my-repo" / "0000000.pickle")
    assert project_definition == {"actions": {"a1": {}, "a2": {}}}
