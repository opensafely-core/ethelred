from app import repositories


def test_repository_get_job_requests(tmp_path):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    # This fixture doesn't have to correspond to whatever tasks/get_job_requests.py
    # would write. It just has to exercise Repository.get_job_requests.
    job_requests_path.write_text("id,sha\n1,1111111\n2,2222222")
    repository = repositories.Repository(tmp_path)
    job_requests = repository.get_job_requests()
    assert list(job_requests["id"]) == [1, 2]
    assert list(job_requests["sha"]) == [1111111, 2222222]


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
