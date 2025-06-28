import collections
import pickle

from tasks import get_project_definitions


Row = collections.namedtuple("Row", ["url", "sha", "project_definition"])


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


def test_write(tmp_path):
    record = get_project_definitions.Record(
        "my-repo", "0000000", {"actions": {"a1": {}, "a2": {}}}
    )
    project_definitions_dir = tmp_path / "project_definitions"

    get_project_definitions.write(record, project_definitions_dir)

    with open(project_definitions_dir / "my-repo" / "0000000.pickle", "rb") as f:
        project_definition = pickle.load(f)

    assert project_definition == {"actions": {"a1": {}, "a2": {}}}
