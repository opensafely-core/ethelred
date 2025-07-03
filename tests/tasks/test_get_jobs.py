import collections
import datetime

from tasks import get_jobs


Row = collections.namedtuple("Row", ["id", "job_request_id", "created_at"])


def test_transform():
    rows = [Row(123, 4567, datetime.datetime(2025, 1, 1))]
    records = list(get_jobs.transform(rows))
    record = records[0]

    assert record.id == 123
    assert record.job_request_id == 4567
    assert record.created_at == datetime.datetime(2025, 1, 1)
