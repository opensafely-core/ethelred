import datetime
import json
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
def test_get_pages(monkeypatch):
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

    pages = get_workflow_runs.get_pages("https://test.url")

    assert isinstance(pages, types.GeneratorType)
    page_1, page_2 = list(pages)
    assert page_1 == ["page", "1", "data"]
    assert page_2 == ["page", "2", "data"]


@responses.activate
def test_extract(tmpdir, monkeypatch):
    # Environment variable only needs to be available; correct usage tested in test_get_pages
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "")

    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos",
        json=[{"name": "repo_1"}],
        headers={"Link": '<https://repos.page2>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://repos.page2",
        json=[{"name": "repo_2"}],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/repo_1/actions/runs",
        json={"total_count": 2, "workflow_runs": [{"id": 1}]},
        headers={"Link": '<https://repo_1/runs.page2>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://repo_1/runs.page2",
        json={"total_count": 2, "workflow_runs": [{"id": 2}]},
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/repo_2/actions/runs",
        json={"total_count": 0, "workflow_runs": []},
    )

    output_dir = pathlib.Path(tmpdir)
    get_workflow_runs.extract("test-org", output_dir, datetime.datetime(2025, 1, 1))

    assert io.read(output_dir / "repos" / "20250101-000000" / "repo_1.json") == {
        "name": "repo_1"
    }
    assert io.read(output_dir / "repos" / "20250101-000000" / "repo_2.json") == {
        "name": "repo_2"
    }
    assert io.read(output_dir / "repos" / "20250101-000000" / "repo_2.json") == {
        "name": "repo_2"
    }
    assert io.read(output_dir / "runs" / "repo_1" / "20250101-000000" / "1.json") == {
        "id": 1
    }
    assert io.read(output_dir / "runs" / "repo_1" / "20250101-000000" / "2.json") == {
        "id": 2
    }


def test_get_names_of_extracted_repos(tmpdir):
    runs_dir = pathlib.Path(tmpdir)
    (runs_dir / "repo_1").mkdir(parents=True)
    (runs_dir / "repo_2").mkdir(parents=True)

    extracted_repos = get_workflow_runs.get_names_of_extracted_repos(runs_dir)

    assert extracted_repos == ["repo_1", "repo_2"]


def test_load_latest_workflow_runs(tmpdir):
    repo_dir = pathlib.Path(tmpdir) / "repo_1"
    older_dir = repo_dir / "20250101-000000"
    older_dir.mkdir(parents=True)
    newer_dir = repo_dir / "20250102-000000"
    newer_dir.mkdir(parents=True)

    (older_dir / "1.json").write_text('{"id": 1,"status": "completed"}')
    (older_dir / "2.json").write_text('{"id": 2, "status": "running"}')
    (newer_dir / "2.json").write_text('{"id": 2, "status": "completed"}')
    (newer_dir / "3.json").write_text('{"id": 3, "status": "running"}')

    runs = get_workflow_runs.load_latest_workflow_runs(repo_dir)

    assert isinstance(runs, types.GeneratorType)
    assert list(runs) == [
        {"id": 3, "status": "running"},
        {"id": 2, "status": "completed"},
        {"id": 1, "status": "completed"},
    ]


def test_get_records(tmpdir):
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
    # Timestamp handling is tested elsewhere so only one timestamp per repo here
    runs_dir = pathlib.Path(tmpdir)
    repo_1_dir = runs_dir / "repo_1" / "20250101-000000"
    repo_2_dir = runs_dir / "repo_2" / "20250101-000000"
    repo_1_dir.mkdir(parents=True)
    repo_2_dir.mkdir(parents=True)

    repo_1_run_1 = template | {"id": 1, "repository": {"name": "repo_1"}}
    (repo_1_dir / "1.json").write_text(json.dumps(repo_1_run_1))
    repo_1_run_2 = template | {"id": 2, "repository": {"name": "repo_1"}}
    (repo_1_dir / "2.json").write_text(json.dumps(repo_1_run_2))
    repo_2_run_3 = template | {"id": 3, "repository": {"name": "repo_2"}}
    (repo_2_dir / "3.json").write_text(json.dumps(repo_2_run_3))

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
    # Environment variable only needs to be available; correct usage tested in test_get_pages
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "")

    # Run through pipeline for a single workflow run
    workflows_dir = pathlib.Path(tmpdir)

    def mock_now(timezone):
        return datetime.datetime(2025, 1, 1, tzinfo=timezone)

    run = {
        "id": 1,
        "name": "My Workflow",
        "head_sha": 12345678,
        "status": "pending",
        "conclusion": None,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "run_started_at": "2025-01-01T00:00:00Z",
        "repository": {"name": "test_repo"},
    }

    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos",
        json=[{"name": "test_repo"}],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/test_repo/actions/runs",
        json={"total_count": 1, "workflow_runs": [run]},
    )

    get_workflow_runs.main("test-org", workflows_dir, now_function=mock_now)

    with open(workflows_dir / "workflow_runs.csv") as f:
        csv_file = f.read()

    assert io.read(workflows_dir / "repos" / "20250101-000000" / "test_repo.json") == {
        "name": "test_repo"
    }
    assert (
        io.read(workflows_dir / "runs" / "test_repo" / "20250101-000000" / "1.json")
        == run
    )
    assert csv_file == (
        "id,repo,name,head_sha,status,conclusion,created_at,updated_at,run_started_at\n"
        "1,test_repo,My Workflow,12345678,pending,,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z\n"
    )
