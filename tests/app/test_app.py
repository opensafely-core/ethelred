import pandas as pd
from streamlit.testing.v1 import AppTest

from app import app


def test_app(tmp_path, monkeypatch):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    job_requests_path.write_text(
        "created_at,num_actions,num_jobs\n2025-01-01 00:00:00.0+00:00,1,1\n"
    )
    jobs_path = tmp_path / "jobs" / "jobs.csv"
    jobs_path.parent.mkdir()
    jobs_path.write_text("job_request_id,outcome\n123,1\n123,2\n")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    app_test = AppTest.from_file("app/app.py")
    app_test.run()

    assert not app_test.exception


def test_calculate_proportions():
    jobs = pd.DataFrame(
        {
            "job_request_id": [123, 123, 123, 456, 456, 789],
            "outcome": [1, 2, 3, 2, 3, 3],
        }
    )
    job_requests = app.calculate_proportions(jobs)
    assert job_requests.to_dict() == {"proportion": {123: 1 / 2, 456: 0.0}}
