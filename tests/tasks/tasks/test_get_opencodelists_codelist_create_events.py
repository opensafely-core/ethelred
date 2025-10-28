import collections
import datetime

from tasks.tasks import get_opencodelists_codelist_create_events


Row = collections.namedtuple("Row", ["created_at", "id"])


def test_get_records():
    row = Row(created_at=datetime.datetime(2025, 1, 1, microsecond=1), id=1)
    records = list(get_opencodelists_codelist_create_events.get_records([row]))
    record = records[0]
    assert record.created_at == datetime.datetime(2025, 1, 1, microsecond=0)
    assert record.id == 1
