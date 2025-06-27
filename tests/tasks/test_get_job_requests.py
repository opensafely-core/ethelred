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


def test_write(tmp_path):
    records = [
        get_job_requests.Record(datetime.datetime(2025, 1, 1), 2, 1),
        get_job_requests.Record(datetime.datetime(2025, 1, 2), 4, 2),
    ]
    f_path = tmp_path / "job_requests" / "job_requests.csv"
    get_job_requests.write(records, f_path)
    assert (
        f_path.read_text()
        == "created_at,num_actions,num_jobs\n"
        + "2025-01-01 00:00:00,2,1\n"
        + "2025-01-02 00:00:00,4,2\n"
    )
