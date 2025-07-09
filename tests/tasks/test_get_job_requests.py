import collections
import datetime

from tasks import get_job_requests, io


Row = collections.namedtuple(
    "Row", ["url", "sha", "created_at", "num_jobs", "username"]
)


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
