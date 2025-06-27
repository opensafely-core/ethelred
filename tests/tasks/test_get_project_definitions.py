import collections

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
