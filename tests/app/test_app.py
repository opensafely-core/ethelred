import pandas
from streamlit.testing.v1 import AppTest

from app import app


class FakeRepository:
    def get_job_requests(self):
        return pandas.DataFrame(
            {
                "num_actions": [1],
                "num_jobs": [1],
                "username": ["a_user"],
            }
        )


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
