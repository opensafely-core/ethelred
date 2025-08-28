import pathlib
import types

import pytest
import responses
import responses.matchers

from tasks import get_workflow_runs, io


@responses.activate
def test_get_with_retry_when_successful(capsys):
    def sleep(seconds):  # pragma: no cover
        # Should not be called but if this test fails,
        # we still don't want time.sleep to be called
        return

    responses.add(responses.GET, "http://test.url", json=["data_1", "data_2"])

    response = get_workflow_runs.get_with_retry("http://test.url", sleep_function=sleep)
    assert response.json() == ["data_1", "data_2"]
    assert capsys.readouterr().out == ""


@responses.activate
def test_get_with_retry_when_fail(capsys):
    def sleep(seconds):
        return

    responses.add(responses.GET, "http://invalid.url", status=400)
    ERROR = "400 Client Error: Bad Request for url: http://invalid.url/"

    with pytest.raises(Exception, match=ERROR):
        get_workflow_runs.get_with_retry("http://invalid.url", sleep_function=sleep)

    assert capsys.readouterr().out == (
        f"Error fetching http://invalid.url: {ERROR}\n"
        "Retrying in 0.5 seconds (retry attempt 1)...\n"
        f"Error fetching http://invalid.url: {ERROR}\n"
        "Retrying in 1.0 seconds (retry attempt 2)...\n"
        f"Error fetching http://invalid.url: {ERROR}\n"
        "Retrying in 2.0 seconds (retry attempt 3)...\n"
        f"Error fetching http://invalid.url: {ERROR}\n"
        "Maximum retries reached (3).\n"
    )


@responses.activate
def test_get_with_retry_when_fail_then_succeed(capsys):
    def sleep(seconds):
        return

    responses.add(responses.GET, "http://flaky.url", status=500)
    responses.add(responses.GET, "http://flaky.url", status=500)
    responses.add(responses.GET, "http://flaky.url", status=500)
    responses.add(responses.GET, "http://flaky.url", json=["data_1", "data_2"])

    response = get_workflow_runs.get_with_retry(
        "http://flaky.url", sleep_function=sleep
    )

    assert response.json() == ["data_1", "data_2"]
    assert capsys.readouterr().out == (
        "Error fetching http://flaky.url: 500 Server Error: Internal Server Error for url: http://flaky.url/\n"
        "Retrying in 0.5 seconds (retry attempt 1)...\n"
        "Error fetching http://flaky.url: 500 Server Error: Internal Server Error for url: http://flaky.url/\n"
        "Retrying in 1.0 seconds (retry attempt 2)...\n"
        "Error fetching http://flaky.url: 500 Server Error: Internal Server Error for url: http://flaky.url/\n"
        "Retrying in 2.0 seconds (retry attempt 3)...\n"
    )


@responses.activate
def test_fetch_pages(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "test_token")
    match = [
        responses.matchers.header_matcher({"Authorization": "Bearer test_token"}),
        responses.matchers.query_param_matcher({"per_page": 100, "format": "json"}),
    ]
    responses.add(
        responses.GET,
        "https://test.url",
        json=["page", "1", "data"],
        match=match,
        headers={"Link": '<https://nextpage.url>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://nextpage.url",
        json=["page", "2", "data"],
        match=match,
    )

    pages = get_workflow_runs.fetch_pages("https://test.url")

    assert isinstance(pages, types.GeneratorType)
    page_1, page_2 = list(pages)
    assert page_1 == ["page", "1", "data"]
    assert page_2 == ["page", "2", "data"]


@responses.activate
def test_extract(tmpdir, monkeypatch):
    # Environment variable only needs to be available; correct usage tested in test_fetch_pages
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "")

    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos",
        json=[
            {
                "name": "repo_1",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ],
        headers={"Link": '<https://repos.page2>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://repos.page2",
        json=[
            {
                "name": "repo_2",
                "updated_at": "2025-01-02T00:00:00Z",
            }
        ],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/repo_1/actions/runs",
        json={
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 1,
                    "updated_at": "2025-01-03T00:00:00Z",
                }
            ],
        },
        headers={"Link": '<https://repo_1/runs.page2>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://repo_1/runs.page2",
        json={
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 2,
                    "updated_at": "2025-01-04T00:00:00Z",
                }
            ],
        },
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/repo_2/actions/runs",
        json={"total_count": 0, "workflow_runs": []},
    )
    output_dir = pathlib.Path(tmpdir)

    get_workflow_runs.extract("test-org", output_dir)

    assert io.read(output_dir / "repos" / "repo_1" / "20250101-000000.json") == {
        "name": "repo_1",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    assert io.read(output_dir / "repos" / "repo_2" / "20250102-000000.json") == {
        "name": "repo_2",
        "updated_at": "2025-01-02T00:00:00Z",
    }
    assert io.read(output_dir / "runs" / "repo_1" / "1" / "20250103-000000.json") == {
        "id": 1,
        "updated_at": "2025-01-03T00:00:00Z",
    }
    assert io.read(output_dir / "runs" / "repo_1" / "2" / "20250104-000000.json") == {
        "id": 2,
        "updated_at": "2025-01-04T00:00:00Z",
    }


def test_filter_workflow_run_filepaths(tmpdir):
    parent = pathlib.Path(tmpdir) / "repo_1"
    filepaths = [
        parent / "1" / "20250101-000000.json",
        parent / "2" / "20250101-000000.json",
        parent / "2" / "20250102-000000.json",
        parent / "3" / "20250102-000000.json",
    ]

    filtered = get_workflow_runs.filter_workflow_run_filepaths(filepaths)

    assert list(filtered) == [
        parent / "3" / "20250102-000000.json",
        parent / "2" / "20250102-000000.json",
        parent / "1" / "20250101-000000.json",
    ]


def test_get_records(tmpdir):
    # Timestamp handling is tested elsewhere so use same updated_at for all runs
    template = {
        "id": None,  # Placeholder
        "name": "My Workflow",
        "head_sha": 12345678,
        "status": "pending",
        "conclusion": None,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "run_started_at": "2025-01-01T00:00:00Z",
        "repository": {
            "name": None  # Placeholder
        },
    }
    runs_dir = pathlib.Path(tmpdir)
    repo_1_run_1 = template | {"id": 1, "repository": {"name": "repo_1"}}
    io.write(repo_1_run_1, runs_dir / "repo_1" / "1" / "20250101-000000.json")
    repo_1_run_2 = template | {"id": 2, "repository": {"name": "repo_1"}}
    io.write(repo_1_run_2, runs_dir / "repo_1" / "2" / "20250101-000000.json")
    repo_2_run_3 = template | {"id": 3, "repository": {"name": "repo_2"}}
    io.write(repo_2_run_3, runs_dir / "repo_2" / "3" / "20250101-000000.json")

    records = get_workflow_runs.get_records(runs_dir)

    record_1, record_2, record_3 = sorted(records, key=lambda r: r.id)
    assert isinstance(records, types.GeneratorType)
    assert record_1._fields == get_workflow_runs.Record._fields
    assert record_1.id == 1
    assert record_1.repo == "repo_1"
    assert record_2.id == 2
    assert record_2.repo == "repo_1"
    assert record_3.id == 3
    assert record_3.repo == "repo_2"


@responses.activate
def test_main(tmpdir, monkeypatch):
    # Environment variable only needs to be available; correct usage tested in test_fetch_pages
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "")
    # Run through pipeline for a single workflow run
    workflows_dir = pathlib.Path(tmpdir)
    run = {
        "id": 1,
        "name": "My Workflow",
        "head_sha": 12345678,
        "status": "pending",
        "conclusion": None,
        "created_at": "2025-01-02T00:00:00Z",
        "updated_at": "2025-01-04T00:00:00Z",
        "run_started_at": "2025-01-03T00:00:00Z",
        "repository": {"name": "test_repo"},
    }
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos",
        json=[{"name": "test_repo", "updated_at": "2025-01-01T00:00:00Z"}],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/test_repo/actions/runs",
        json={"total_count": 1, "workflow_runs": [run]},
    )

    get_workflow_runs.main("test-org", workflows_dir)
    with open(workflows_dir / "workflow_runs.csv") as f:
        csv_file = f.read()

    assert io.read(workflows_dir / "repos" / "test_repo" / "20250101-000000.json") == {
        "name": "test_repo",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    assert (
        io.read(workflows_dir / "runs" / "test_repo" / "1" / "20250104-000000.json")
        == run
    )
    assert csv_file == (
        "id,repo,name,head_sha,status,conclusion,created_at,updated_at,run_started_at\n"
        "1,test_repo,My Workflow,12345678,pending,,2025-01-02T00:00:00Z,2025-01-04T00:00:00Z,2025-01-03T00:00:00Z\n"
    )
