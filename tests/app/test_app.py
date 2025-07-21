import datetime

import pandas
from streamlit.testing.v1 import AppTest

from app import app, repositories


class FakeRepository(repositories.AbstractRepository):
    def get_date_earliest_job_request_created(self):
        return datetime.datetime(2025, 1, 1)

    def get_date_latest_job_request_created(self):
        return datetime.datetime(2025, 2, 1)

    def get_job_requests(self, from_, to_):
        return pandas.DataFrame(
            {
                "created_at": [
                    datetime.datetime(2025, 1, 1),
                    datetime.datetime(2025, 2, 1),
                ],
                "num_actions": [1, 1],
                "num_jobs": [1, 1],
                "username": ["a_user", "a_user"],
            }
        )

    def get_jobs(self): ...  # pragma: no cover


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
