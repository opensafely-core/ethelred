import datetime
import json
import pathlib
import types

from tasks import get_workflow_runs


class MockResponse:
    def __init__(self, json_data, next_url=None):
        self.links = {"next": {"url": next_url}} if next_url else {}
        self.json_data = json_data
        self.status_code = 200

    def json(self):
        return self.json_data

    def raise_for_status(self):
        pass  # Response is valid


class MockErrorResponse:
    def __init__(self, error):
        self.error = error
        self.status_code = 400

    def raise_for_status(self):
        raise Exception(self.error)


def test_github_api_session_init(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "test_token")
    session = get_workflow_runs.GitHubAPISession()

    assert session.headers["Authorization"] == "Bearer test_token"
    assert session.params == {"per_page": 100, "format": "json"}

    session.close()


def test_session_with_retry_when_successful(capsys):
    def sleep(seconds):  # pragma: no cover
        # Should not be called but if this test fails,
        # we still don't want time.sleep to be called
        return

    session = {"test_url": MockResponse(["data_1", "data_2"])}
    session_with_retry = get_workflow_runs.SessionWithRetry(
        session, 3, 0.5, sleep_function=sleep
    )

    response = session_with_retry.get("test_url")
    assert response.json() == ["data_1", "data_2"]
    assert capsys.readouterr().out == ""


def test_session_with_retry_when_fail(capsys):
    def sleep(seconds):
        return

    session = {"invalid_url": MockErrorResponse("Network error")}
    session_with_retry = get_workflow_runs.SessionWithRetry(
        session, 3, 0.5, sleep_function=sleep
    )
    response = session_with_retry.get("invalid_url")
    assert response.status_code == 400
    assert capsys.readouterr().out == (
        "Error fetching invalid_url: Network error\n"
        "Retrying in 0.5 seconds (retry attempt 1)...\n"
        "Error fetching invalid_url: Network error\n"
        "Retrying in 1.0 seconds (retry attempt 2)...\n"
        "Error fetching invalid_url: Network error\n"
        "Retrying in 2.0 seconds (retry attempt 3)...\n"
        "Error fetching invalid_url: Network error\n"
        "Maximum retries reached (3).\n"
    )


def test_session_with_retry_when_fail_then_succeed(capsys):
    def sleep(seconds):
        return

    responses = {
        "flaky_url": [MockErrorResponse("Temporary failure")] * 3
        + [MockResponse(["data_1", "data_2"])]
    }

    class MockSession:
        def get(self, url):
            return responses[url].pop(0)

    session = MockSession()
    session_with_retry = get_workflow_runs.SessionWithRetry(
        session, 3, 0.5, sleep_function=sleep
    )
    response = session_with_retry.get("flaky_url")

    assert response.json() == ["data_1", "data_2"]
    assert capsys.readouterr().out == (
        "Error fetching flaky_url: Temporary failure\nRetrying in 0.5 seconds (retry attempt 1)...\n"
        "Error fetching flaky_url: Temporary failure\nRetrying in 1.0 seconds (retry attempt 2)...\n"
        "Error fetching flaky_url: Temporary failure\nRetrying in 2.0 seconds (retry attempt 3)...\n"
    )


def test_get_pages():
    session = {
        "repos?page=1": MockResponse(["page", "1", "data"], next_url="repos?page=2"),
        "repos?page=2": MockResponse(["page", "2", "data"]),
    }
    pages = get_workflow_runs.get_pages(session, "repos?page=1")

    assert isinstance(pages, types.GeneratorType)
    page_1, page_2 = list(pages)
    assert page_1.json_data == ["page", "1", "data"]
    assert page_2.json_data == ["page", "2", "data"]


def test_get_repos():
    page_1 = MockResponse([{"name": "repo_1"}], next_url="repos?page=2")
    page_2 = MockResponse([{"name": "repo_2"}])
    session = {
        f"https://api.github.com/orgs/{get_workflow_runs.GITHUB_ORG}/repos": page_1,
        "repos?page=2": page_2,
    }
    repos = get_workflow_runs.get_repos(session)

    assert list(repos) == [{"name": "repo_1"}, {"name": "repo_2"}]


def test_get_repo_workflow_runs():
    page_1 = MockResponse(
        {"total_count": 2, "workflow_runs": [{"id": 1}]}, next_url="page_2_url"
    )
    page_2 = MockResponse({"total_count": 2, "workflow_runs": [{"id": 2}]})
    session = {
        f"https://api.github.com/repos/{get_workflow_runs.GITHUB_ORG}/repo_1/actions/runs": page_1,
        "page_2_url": page_2,
    }
    workflow_runs = get_workflow_runs.get_repo_workflow_runs("repo_1", session)

    assert list(workflow_runs) == [{"id": 1}, {"id": 2}]


def test_extract():
    mock_file_system = {}

    def mock_write(obj, f_path):
        mock_file_system[str(f_path)] = obj

    repos_page_1 = MockResponse([{"name": "repo_1"}], next_url="repos?page=2")
    repos_page_2 = MockResponse([{"name": "repo_2"}])
    repo_1_runs_page = MockResponse(
        {"total_count": 2, "workflow_runs": [{"id": 1}, {"id": 2}]}
    )
    repo_2_runs_page = MockResponse({"total_count": 0, "workflow_runs": []})
    session = {
        f"https://api.github.com/orgs/{get_workflow_runs.GITHUB_ORG}/repos": repos_page_1,
        "repos?page=2": repos_page_2,
        f"https://api.github.com/repos/{get_workflow_runs.GITHUB_ORG}/repo_1/actions/runs": repo_1_runs_page,
        f"https://api.github.com/repos/{get_workflow_runs.GITHUB_ORG}/repo_2/actions/runs": repo_2_runs_page,
    }
    output_dir = pathlib.Path("test_dir")
    get_workflow_runs.extract(
        session, output_dir, datetime.datetime(2025, 1, 1), mock_write
    )

    assert mock_file_system == {
        "test_dir/repos/20250101-000000Z/repo_1.json": '{"name": "repo_1"}',
        "test_dir/repos/20250101-000000Z/repo_2.json": '{"name": "repo_2"}',
        "test_dir/runs/repo_1/20250101-000000Z/1.json": '{"id": 1}',
        "test_dir/runs/repo_1/20250101-000000Z/2.json": '{"id": 2}',
    }


def test_get_names_of_extracted_repos(tmpdir):
    runs_dir = pathlib.Path(tmpdir)
    (runs_dir / "repo_1").mkdir(parents=True)
    (runs_dir / "repo_2").mkdir(parents=True)

    extracted_repos = get_workflow_runs.get_names_of_extracted_repos(runs_dir)

    assert extracted_repos == ["repo_1", "repo_2"]


def test_load_latest_workflow_runs(tmpdir):
    repo_dir = pathlib.Path(tmpdir) / "repo_1"
    older_dir = repo_dir / "20250101-000000Z"
    older_dir.mkdir(parents=True)
    newer_dir = repo_dir / "20250102-000000Z"
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
    repo_1_dir = runs_dir / "repo_1" / "20250101-000000Z"
    repo_2_dir = runs_dir / "repo_2" / "20250101-000000Z"
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


def test_main(tmpdir):
    # Run through pipeline for a single workflow run
    workflows_dir = pathlib.Path(tmpdir)

    def mock_now():
        return datetime.datetime(2025, 1, 1)

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

    repos_page = MockResponse([{"name": "test_repo"}])
    repo_1_runs_page = MockResponse({"total_count": 1, "workflow_runs": [run]})

    session = {
        f"https://api.github.com/orgs/{get_workflow_runs.GITHUB_ORG}/repos": repos_page,
        f"https://api.github.com/repos/{get_workflow_runs.GITHUB_ORG}/test_repo/actions/runs": repo_1_runs_page,
    }

    get_workflow_runs.main(session, workflows_dir, now_function=mock_now)

    with open(workflows_dir / "repos" / "20250101-000000Z" / "test_repo.json") as f:
        repo_page = json.load(f)

    with open(
        workflows_dir / "runs" / "test_repo" / "20250101-000000Z" / "1.json"
    ) as f:
        run_file = json.load(f)

    with open(workflows_dir / "workflow_runs.csv") as f:
        csv_file = f.read()

    assert repo_page == {"name": "test_repo"}
    assert run_file == run
    assert csv_file == (
        "id,repo,name,head_sha,status,conclusion,created_at,updated_at,run_started_at\n"
        "1,test_repo,My Workflow,12345678,pending,,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z\n"
    )
