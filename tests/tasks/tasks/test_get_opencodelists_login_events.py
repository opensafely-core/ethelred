import collections
import datetime

from tasks import utils
from tasks.tasks import get_opencodelists_login_events


Row = collections.namedtuple("Row", ["last_login", "email"])


def test_get_records():
    row = Row(
        last_login=datetime.datetime(2025, 1, 1, microsecond=1),
        email="user@example.com",
    )
    records = list(get_opencodelists_login_events.get_records([row]))
    record = records[0]
    assert record.logged_in_at == datetime.datetime(2025, 1, 1, microsecond=0)
    assert record.email_hash == utils.sha256("user@example.com")
