from streamlit.testing.v1 import AppTest


def test_app(tmp_path, monkeypatch):
    tmp_f_path = tmp_path / "job_requests" / "job_requests.csv"
    tmp_f_path.parent.mkdir()
    tmp_f_path.write_text(
        "created_at,num_actions,num_jobs\n2025-01-01 00:00:00.0+00:00,1,1\n"
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    app_test = AppTest.from_file("app/app.py")
    app_test.run()

    assert not app_test.exception
