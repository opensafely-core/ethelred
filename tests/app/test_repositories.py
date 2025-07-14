from app import repositories


def test_get_job_requests(tmp_path):
    job_requests_path = tmp_path / "job_requests" / "job_requests.csv"
    job_requests_path.parent.mkdir()
    job_requests_path.write_text(
        "created_at,num_actions,num_jobs\n2025-01-01 00:00:00.0+00:00,1,1\n"
    )
    repository = repositories.Repository(tmp_path)
    job_requests = repository.get_job_requests()
    assert list(job_requests["measure"]) == [1]
