import datetime

import pandas
from streamlit.testing.v1 import AppTest

from app import app, repositories


class FakeRepository(repositories.AbstractRepository):
    def get_earliest_login_date(self):
        return datetime.date(2025, 1, 1)

    def get_latest_login_date(self):
        return datetime.date(2025, 1, 1)

    def get_logins_per_day(self, from_, to_):
        return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
