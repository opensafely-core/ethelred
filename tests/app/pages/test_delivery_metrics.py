import datetime

import pandas
import pytest
from streamlit.testing.v1 import AppTest

from pages.delivery_metrics import Repository, main


@pytest.mark.slow
def test_app():
    class FakeRepository:
        def get_prs_created_per_day(self):
            return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})

    app_test = AppTest.from_function(main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception


def test_get_prs_created_per_day(tmp_path):
    prs_csv = tmp_path / "prs.csv"
    prs_csv.write_text(
        "number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
        + "1,author,2024-01-17T00:00:00Z,,,,False\n"
        + "2,author,2024-01-18T01:00:00Z,,,,False\n"
        + "3,author,2024-01-18T02:00:00Z,,,,False\n"
        + "4,author,2024-01-20T00:00:00Z,,,,False\n"
    )
    repository = Repository(prs_csv.as_uri())
    obs = repository.get_prs_created_per_day()
    exp = pandas.DataFrame(
        {
            "date": [
                datetime.datetime(2024, 1, 17),
                datetime.datetime(2024, 1, 18),
                datetime.datetime(2024, 1, 19),  # interpolated zero
                datetime.datetime(2024, 1, 20),
            ],
            "count": [1, 2, 0, 1],
        }
    )
    pandas.testing.assert_frame_equal(obs, exp)
