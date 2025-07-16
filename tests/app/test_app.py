import datetime

import pandas
from streamlit.testing.v1 import AppTest

from app import app, repositories


class FakeRepository(repositories.AbstractRepository):
    def get_job_requests(self):
        return pandas.DataFrame(
            {
                "id": [1],
                "created_at": [datetime.datetime(2025, 1, 1)],
                "num_actions": [1],
                "num_jobs": [1],
                "num_jobs_over_num_actions": [1],
            }
        )

    def get_jobs(self):
        return pandas.DataFrame(
            {
                "job_request_id": [123, 123],
                "outcome": ["errored", "cancelled by dependency"],
            }
        )

    @staticmethod
    def calculate_proportions(jobs):
        return repositories.Repository.calculate_proportions(jobs)


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
