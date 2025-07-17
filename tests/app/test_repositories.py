from app import repositories


def test_repository_get_job_requests(tmp_path):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    job_requests_path.write_text(
        "created_at,num_actions,num_jobs,username,measure\n"
        + "2025-01-01 00:00:00.0+00:00,1,1,a_user,1\n"
    )
    repository = repositories.Repository(tmp_path)
    job_requests = repository.get_job_requests()
    # `Repository.get_job_requests` is a wrapper for pandas.read_csv, so there's not
    # much to test. Nevertheless, it's important that it is tested. Let's start by
    # testing the column index labels.
    assert list(job_requests.columns) == [
        "created_at",
        "num_actions",
        "num_jobs",
        "username",
        "measure",
    ]


def test_repository_get_jobs(tmp_path):
    jobs_path = tmp_path / "jobs" / "jobs.csv"
    jobs_path.parent.mkdir()
    jobs_path.write_text(
        "job_request_id,outcome\n123,errored\n123,cancelled by dependency\n"
    )
    repository = repositories.Repository(tmp_path)
    jobs = repository.get_jobs()
    assert list(jobs["job_request_id"]) == [123, 123]
    assert list(jobs["outcome"]) == ["errored", "cancelled by dependency"]
