import collections
import datetime
import pickle

from tasks import get_job_requests


Row = collections.namedtuple("Row", ["url", "sha", "created_at", "num_jobs"])


def test_load_project_definition(tmp_path):
    f_path = tmp_path / "my-repo" / "0000000.pickle"
    f_path.parent.mkdir()
    with f_path.open("wb") as f:
        pickle.dump({}, f)
    project_definition = get_job_requests.load_project_definition(
        tmp_path, "my-repo", "0000000"
    )
    assert project_definition == {}


def test_get_record():
    row = Row(
        "https://github.com/opensafely/my-repo",
        "0000000",
        datetime.datetime(2025, 1, 1),
        1,
    )
    project_definition = {"actions": {"a1": {}, "a2": {}}}
    record = get_job_requests.get_record(row, project_definition)
    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.num_actions == 2
    assert record.num_jobs == 1


def test_transform():
    row = Row(
        "https://github.com/opensafely/my-repo",
        "0000000",
        datetime.datetime(2025, 1, 1),
        1,
    )

    def load_project_definition(repo, sha):
        return {"actions": {"a1": {}, "a2": {}}}

    records = list(get_job_requests.transform([row], load_project_definition))
    record = records[0]

    assert record.created_at == datetime.datetime(2025, 1, 1)
    assert record.num_actions == 2
    assert record.num_jobs == 1
