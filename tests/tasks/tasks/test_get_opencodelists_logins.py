import collections
import datetime

from tasks import utils
from tasks.tasks import get_opencodelists_logins


Row = collections.namedtuple("Row", ["last_login", "email"])


def test_get_records():
    row = Row(
        last_login=datetime.datetime(2025, 1, 1, tzinfo=None),
        email="user@example.com",
    )
    records = list(get_opencodelists_logins.get_records([row]))
    record = records[0]

    assert record.login_at == datetime.datetime(
        2025, 1, 1, tzinfo=datetime.timezone.utc
    )
    assert record.email_hash == utils.sha256("user@example.com")
