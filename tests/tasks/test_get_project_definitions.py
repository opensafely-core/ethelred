import collections
import datetime

import sqlalchemy

from tasks import get_project_definitions, io


Row = collections.namedtuple("Row", ["url", "sha", "project_definition"])


def test_get_query(
    jobserver_engine,
    jobserver_metadata,
    example_repo,
    example_workspace,
    make_jobrequest,
):
    # arrange
    repo_table = jobserver_metadata.tables["jobserver_repo"]
    insert_into_repo_table = sqlalchemy.insert(repo_table).values(example_repo)

    workspace_table = jobserver_metadata.tables["jobserver_workspace"]
    insert_into_workspace_table = sqlalchemy.insert(workspace_table).values(
        example_workspace,
    )

    jobrequest_table = jobserver_metadata.tables["jobserver_jobrequest"]
    # before index date
    jobrequest_1 = make_jobrequest(
        id_=1,
        created_at=datetime.datetime(2024, 1, 1),
        workspace_id=example_workspace["id"],
        sha="0000000",
        project_definition="actions: {a1: {}, a2: {}}",
    )
    # on or after index date
    jobrequest_2 = make_jobrequest(
        id_=2,
        created_at=datetime.datetime(2025, 1, 1),
        workspace_id=example_workspace["id"],
        sha="0000000",
        project_definition="actions: {a1: {}, a2: {}}",
    )
    insert_into_jobrequest_table = sqlalchemy.insert(jobrequest_table).values(
        [jobrequest_1, jobrequest_2]
    )

    with jobserver_engine.connect() as conn:
        conn.execute(insert_into_repo_table)
        conn.execute(insert_into_workspace_table)
        conn.execute(insert_into_jobrequest_table)
        conn.commit()

    # act
    query = get_project_definitions.get_query(jobserver_metadata)
    with jobserver_engine.connect() as conn:
        rows = list(conn.execute(query))

    # assert
    assert len(rows) == 1
    row = rows[0]
    assert row.url == "https://github.com/opensafely/my-repo"
    assert row.sha == "0000000"
    assert row.project_definition == "actions: {a1: {}, a2: {}}"


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
