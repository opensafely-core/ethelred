import collections
import datetime

from tasks import get_job_requests


Row = collections.namedtuple("Row", ["url", "sha", "created_at", "num_jobs"])


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
