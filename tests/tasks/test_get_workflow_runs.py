import pathlib

import requests

from tasks import get_workflow_runs, io


class MockResponse:
    def __init__(self, json_data, next_url="", error=""):
        self.links = {"next": {"url": next_url}} if next_url else {}
        self.json_data = json_data
        self.error = error
        self.status_code = 200 if not error else 404

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.error:
            raise requests.HTTPError(self.error)


def test_github_api_session_init(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW_RUNS_TOKEN", "test_token")
    session = get_workflow_runs.GitHubAPISession()
    assert session.headers["Authorization"] == "Bearer test_token"


def test_github_api_session_init_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_WORKFLOW_RUNS_TOKEN", raising=False)
    session = get_workflow_runs.GitHubAPISession()
    assert "Authorization" not in session.headers


def test_retry_when_all_fail(monkeypatch):
    logs = []
    sleep_call_args = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_call_args.append(seconds))

    @get_workflow_runs.retry(logs.append)
    def get(url, **kwargs):
        return MockResponse({"error": "Not Found"}, error="Not Found")

    response = get("failure_url")

    assert response.json() == {"error": "Not Found"}
    assert sleep_call_args == [0.5, 1.0, 2.0]
    assert logs == [
        "Error fetching failure_url: Not Found\nRetrying in 0.5 seconds (retry attempt 1) ...",
        "Error fetching failure_url: Not Found\nRetrying in 1.0 seconds (retry attempt 2) ...",
        "Error fetching failure_url: Not Found\nRetrying in 2.0 seconds (retry attempt 3) ...",
        "Error fetching failure_url: Not Found\nMaximum retries reached (3).",
    ]


def test_retry_when_successful_first_time():
    logs = []

    @get_workflow_runs.retry(logs.append)
    def get(url, **kwargs):
        return MockResponse({"data": ""})

    response = get("success_url")

    assert response.json() == {"data": ""}
    assert logs == []


def test_retry_when_successful_after_failure(monkeypatch):
    logs = []
    sleep_call_args = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_call_args.append(seconds))
    responses = [
        MockResponse({}, error="Temporary failure"),
        MockResponse({}, error="Temporary failure"),
        MockResponse({"data": ""}),
    ]

    @get_workflow_runs.retry(logs.append)
    def get(url, **kwargs):
        return responses.pop(0)

    response = get("flaky_url")

    assert response.json() == {"data": ""}
    assert sleep_call_args == [0.5, 1.0]
    assert logs == [
        "Error fetching flaky_url: Temporary failure\nRetrying in 0.5 seconds (retry attempt 1) ...",
        "Error fetching flaky_url: Temporary failure\nRetrying in 1.0 seconds (retry attempt 2) ...",
    ]


def test_write_page(tmpdir):
    output_dir = pathlib.Path(tmpdir)
    get_workflow_runs.write_page([{"id": 1}, {"id": 2}], output_dir, 1)

    page = io.read(output_dir / "pages" / "page_1.json")
    assert page == [{"id": 1}, {"id": 2}]


def test_write_run(tmpdir):
    output_dir = pathlib.Path(tmpdir)
    get_workflow_runs.write_run({"id": 1}, output_dir)

    run = io.read(output_dir / "runs" / "1.json")
    assert run == {"id": 1}


def test_get_all_pages_with_retry():
    urls_called = []
    responses = [
        MockResponse({"data": "page1"}, next_url="page2_url"),
        MockResponse({"data": "page2"}),
    ]

    def get(url, **kwargs):
        urls_called.append(url)
        return responses.pop(0)

    pages = list(get_workflow_runs.get_all_pages_with_retry(get, "start_url"))

    assert urls_called == ["start_url", "page2_url"]
    assert len(pages) == 2
    assert pages[0].json() == {"data": "page1"}
    assert pages[1].json() == {"data": "page2"}


def test_get_all_pages_with_retry_when_failed(monkeypatch):
    logs = []
    monkeypatch.setattr(get_workflow_runs, "write_log", logs.append)
    sleep_call_args = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_call_args.append(seconds))
    urls_called = []
    responses = [
        MockResponse({"data": "page1"}, next_url="page2_url"),
        MockResponse({"error": "Network error"}, error="Network error"),  # initial
        MockResponse({"error": "Network error"}, error="Network error"),  # retry 1
        MockResponse({"error": "Network error"}, error="Network error"),  # retry 2
        MockResponse({"error": "Network error"}, error="Network error"),  # retry 3
    ]

    def get(url, **kwargs):
        urls_called.append(url)
        return responses.pop(0)

    pages = list(get_workflow_runs.get_all_pages_with_retry(get, "start_url"))

    assert urls_called == ["start_url"] + ["page2_url"] * 4
    assert len(pages) == 1
    assert pages[0].json() == {"data": "page1"}
    assert sleep_call_args == [0.5, 1.0, 2.0]
    assert logs == [
        "Error fetching page2_url: Network error\nRetrying in 0.5 seconds (retry attempt 1) ...",
        "Error fetching page2_url: Network error\nRetrying in 1.0 seconds (retry attempt 2) ...",
        "Error fetching page2_url: Network error\nRetrying in 2.0 seconds (retry attempt 3) ...",
        "Error fetching page2_url: Network error\nMaximum retries reached (3).",
        "Skipping.",
    ]


def test_get_repos_pages():
    class MockSession:
        def get(self, url, **kwargs):
            return MockResponse([{"name": "repo1"}, {"name": "repo2"}])

    pages = list(get_workflow_runs.get_repos_pages(MockSession()))
    assert pages == [[{"name": "repo1"}, {"name": "repo2"}]]


def test_get_workflow_runs_pages():
    urls_called = []
    responses = [
        MockResponse(
            {"total_count": 3, "workflow_runs": [{"id": 1}, {"id": 2}]},
            next_url="page2_url",
        ),
        MockResponse({"total_count": 3, "workflow_runs": [{"id": 3}]}),
    ]

    class MockSession:
        def get(self, url, **kwargs):
            urls_called.append(url)
            return responses.pop(0)

    pages = list(get_workflow_runs.get_workflow_runs_pages("my_repo", MockSession()))

    assert urls_called == [
        "https://api.github.com/repos/opensafely/my_repo/actions/runs",
        "page2_url",
    ]
    assert pages == [[{"id": 1}, {"id": 2}], [{"id": 3}]]


def test_get_latest_run_filepaths(tmpdir):
    repo_dir = pathlib.Path(tmpdir)
    io.write({"id": 1}, repo_dir / "1000" / "runs" / "1.json")
    io.write({"id": 2}, repo_dir / "1000" / "runs" / "2.json")
    io.write({"id": 2}, repo_dir / "2000" / "runs" / "2.json")

    filepaths = get_workflow_runs.get_latest_run_filepaths(repo_dir)

    assert filepaths == [
        repo_dir / "1000" / "runs" / "1.json",
        repo_dir / "2000" / "runs" / "2.json",
    ]


def test_get_record():
    run = {
        "id": 1,
        "repository": {"name": "my_repo"},
        "name": "My Workflow",
        "head_sha": "00000000",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "run_started_at": "2025-01-01T00:00:00Z",
    }
    record = get_workflow_runs.get_record(run)
    assert record._fields == get_workflow_runs.Record._fields
    assert record.id == 1
    assert record.repo == "my_repo"


def test_main(monkeypatch, tmpdir):
    workflows_dir = pathlib.Path(tmpdir)
    repos_dir = workflows_dir / "repos"
    repo_1_dir = workflows_dir / "repo_1"
    repo_2_dir = workflows_dir / "repo_2"
    urls_called = []
    run = {
        "id": 1,
        "repository": {"name": "repo_2"},
        "name": "My Workflow",
        "head_sha": "00000000",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "run_started_at": "2025-01-01T00:00:00Z",
    }
    responses = {
        "https://api.github.com/orgs/opensafely/repos": MockResponse(
            [{"name": "repo_1"}, {"name": "repo_2"}]
        ),
        "https://api.github.com/repos/opensafely/repo_1/actions/runs": MockResponse(
            {"total_count": 0, "workflow_runs": []}
        ),
        "https://api.github.com/repos/opensafely/repo_2/actions/runs": MockResponse(
            {"total_count": 1, "workflow_runs": [run]}
        ),
    }

    class MockSession:
        def get(self, url, **kwargs):
            urls_called.append(url)
            return responses.get(url)

    with monkeypatch.context() as m:
        m.setattr("time.time", lambda: 1000.1)
        get_workflow_runs.main(MockSession(), workflows_dir)

    assert urls_called == [
        "https://api.github.com/orgs/opensafely/repos",
        "https://api.github.com/repos/opensafely/repo_1/actions/runs",
        "https://api.github.com/repos/opensafely/repo_2/actions/runs",
    ]
    assert io.read(repos_dir / "1000" / "pages" / "page_1.json") == [
        {"name": "repo_1"},
        {"name": "repo_2"},
    ]
    assert io.read(repo_1_dir / "1000" / "pages" / "page_1.json") == []
    assert io.read(repo_2_dir / "1000" / "pages" / "page_1.json") == [run]
    assert io.read(repo_2_dir / "1000" / "runs" / "1.json") == run
    with open(workflows_dir / "workflow_runs.csv", "r") as f:
        assert f.read() == (
            ",".join(get_workflow_runs.Record._fields) + "\n"
            "1,repo_2,My Workflow,00000000,completed,success,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z\n"
        )
