from app import repositories


def test_repository_get_job_requests(tmp_path):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    # This fixture doesn't have to correspond to whatever tasks/get_job_requests.py
    # would write. It just has to exercise Repository.get_job_requests.
    job_requests_path.write_text(
        "id,created_at\n"
        + "1,2025-01-01T00:00:00Z\n"
        + "2,2025-03-01T00:00:00Z\n"
        + "3,2025-06-01T00:00:00Z\n"
    )
    repository = repositories.Repository(tmp_path)
    job_requests = repository.get_job_requests()
    assert list(job_requests["id"]) == [1, 2, 3]
    # Accessing .dt on a series that doesn't contain datetimelike values will raise an
    # AttributeError. The assertion isn't important; it's here because we expect to see
    # an assertion.
    assert job_requests["created_at"].dt.name == "created_at"


def test_repository_get_jobs(tmp_path):
    jobs_path = tmp_path / "jobs" / "jobs.csv"
    jobs_path.parent.mkdir()
    # This fixture doesn't have to correspond to whatever tasks/get_jobs.py
    # would write. It just has to exercise Repository.get_jobs.
    jobs_path.write_text("id,job_request_id\n1,3\n2,4")
    repository = repositories.Repository(tmp_path)
    jobs = repository.get_jobs()
    assert list(jobs["id"]) == [1, 2]
    assert list(jobs["job_request_id"]) == [3, 4]
