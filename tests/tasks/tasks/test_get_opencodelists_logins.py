import collections
import datetime

import pytest

from tasks import utils
from tasks.tasks import get_opencodelists_logins


Row = collections.namedtuple("Row", ["last_login", "email"])


@pytest.mark.parametrize(
    "last_login,login_at",
    [
        (
            datetime.datetime(2025, 1, 1, tzinfo=None),
            datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
        ),
        pytest.param(None, None, marks=pytest.mark.xfail(raises=AttributeError)),
    ],
)
def test_get_records(last_login, login_at):
    row = Row(last_login=last_login, email="user@example.com")
    records = list(get_opencodelists_logins.get_records([row]))
    record = records[0]
    assert record.login_at == login_at
    assert record.email_hash == utils.sha256("user@example.com")
