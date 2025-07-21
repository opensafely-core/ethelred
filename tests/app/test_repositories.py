import datetime

import pytest

from app import repositories


@pytest.fixture
def repository(tmp_path):
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

    jobs_path = tmp_path / "jobs" / "jobs.csv"
    jobs_path.parent.mkdir()
    # This fixture doesn't have to correspond to whatever tasks/get_jobs.py
    # would write. It just has to exercise Repository.get_jobs.
    jobs_path.write_text("id,job_request_id\n" + "10,1\n" + "20,2\n" + "30,3")

    return repositories.Repository(tmp_path)


def test_get_earliest_job_request_created_at(repository):
    created_at = repository.get_earliest_job_request_created_at()
    assert created_at.date() == datetime.date(2025, 1, 1)


def test_get_latest_job_request_created_at(repository):
    created_at = repository.get_latest_job_request_created_at()
    assert created_at.date() == datetime.date(2025, 6, 1)


def test_repository_get_job_requests(repository):
    job_requests = repository.get_job_requests()
    assert list(job_requests["id"]) == [1, 2, 3]
    # Accessing .dt on a series that doesn't contain datetimelike values will raise an
    # AttributeError. The assertion isn't important; it's here because we expect to see
    # an assertion.
    assert job_requests["created_at"].dt.name == "created_at"


def test_repository_get_jobs(repository):
    jobs = repository.get_jobs()
    assert list(jobs["id"]) == [10, 20, 30]
    assert list(jobs["job_request_id"]) == [1, 2, 3]
