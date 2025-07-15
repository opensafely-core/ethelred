from streamlit.testing.v1 import AppTest


def test_app(tmp_path, monkeypatch):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    job_requests_path.write_text(
        "created_at,num_actions,num_jobs\n2025-01-01 00:00:00.0+00:00,1,1\n"
    )
    jobs_path = tmp_path / "jobs" / "jobs.csv"
    jobs_path.parent.mkdir()
    jobs_path.write_text(
        "job_request_id,outcome\n123,errored\n123,cancelled by dependency\n"
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    app_test = AppTest.from_file("app/app.py")
    app_test.run()

    assert not app_test.exception
