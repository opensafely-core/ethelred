import collections

from tasks import get_jobs


Row = collections.namedtuple("Row", [])


def test_transform():
    rows = [Row()]
    records = list(get_jobs.transform(rows))
    record = records[0]
    assert record == get_jobs.Record()
