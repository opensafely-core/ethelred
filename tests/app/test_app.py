import datetime

import pandas
from streamlit.testing.v1 import AppTest

from app import app


class FakeRepository:
    def get_earliest_login_event_date(self):
        return datetime.date(2025, 1, 1)

    def get_latest_login_event_date(self):
        return datetime.date(2025, 1, 1)

    def get_login_events_per_day(self, from_, to_):
        return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})

    def get_num_users_logged_in_per_day(self, from_, to_):
        return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})

    def get_num_users_logged_in(self, from_, to_):
        return 1_000

    def get_codelist_create_events_per_day(self, from_, to_):
        return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})

    def get_num_codelists_created(self, from_, to_):
        return 1_000


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
