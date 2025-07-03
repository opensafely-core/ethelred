import collections

from tasks import get_jobs


Row = collections.namedtuple("Row", ["id", "job_request_id"])


def test_transform():
    rows = [Row(123, 4567)]
    records = list(get_jobs.transform(rows))
    record = records[0]

    assert record.id == 123
    assert record.job_request_id == 4567
