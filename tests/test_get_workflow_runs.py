import pathlib

import requests

from tasks import get_workflow_runs


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


def test_retry_when_all_fail():
    logs = []

    @get_workflow_runs.retry(logs.append)
    def get(url, **kwargs):
        return MockResponse({}, error="Not Found")

    get("failure_url")

    assert logs == [
        "Error fetching failure_url: Not Found\nRetrying in 0.5 seconds (retry attempt 1) ...",
        "Error fetching failure_url: Not Found\nRetrying in 1.0 seconds (retry attempt 2) ...",
        "Error fetching failure_url: Not Found\nRetrying in 2.0 seconds (retry attempt 3) ...",
        "Error fetching failure_url: Not Found\nSkipping as maximum retries reached (3).",
    ]


def test_retry_when_successful_first_time():
    logs = []

    @get_workflow_runs.retry(logs.append)
    def get(url, **kwargs):
        return MockResponse({"data": ""})

    response = get("success_url")

    assert response.json() == {"data": ""}
    assert logs == []


def test_retry_when_successful_after_failure():
    logs = []
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
    assert logs == [
        "Error fetching flaky_url: Temporary failure\nRetrying in 0.5 seconds (retry attempt 1) ...",
        "Error fetching flaky_url: Temporary failure\nRetrying in 1.0 seconds (retry attempt 2) ...",
    ]


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


def test_get_all_pages_with_retry_when_failed():
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


def test_get_repo_names(monkeypatch, capsys):
    repos = [{"name": "repo1"}, {"name": "repo2"}]

    class MockSession:
        def get(self, url, **kwargs):
            return MockResponse(repos)

    with monkeypatch.context() as m:
        m.setattr("time.time", lambda: 1000.1)
        m.setattr(get_workflow_runs, "DATA_DIR", pathlib.Path("data"))

        repo_names = list(get_workflow_runs.get_repo_names(MockSession()))

    assert repo_names == ["repo1", "repo2"]
    # write_json is currently just a placeholder that prints to the console
    assert capsys.readouterr().out == (
        "Writing a list of 2 items to data/workflow_runs/repos/1000/pages/page_1.json\n"
    )


def test_write_workflow_runs(monkeypatch, capsys):
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

    with monkeypatch.context() as m:
        m.setattr("time.time", lambda: 1000.1)
        m.setattr(get_workflow_runs, "DATA_DIR", pathlib.Path("data"))

        get_workflow_runs.write_workflow_runs("my_repo", MockSession())

    assert urls_called == [
        "https://api.github.com/repos/opensafely/my_repo/actions/runs",
        "page2_url",
    ]
    # write_json is currently just a placeholder that prints to the console
    assert capsys.readouterr().out == (
        "Writing a list of 2 items to data/workflow_runs/my_repo/1000/pages/page_1.json\n"
        "Writing a dict of 1 items to data/workflow_runs/my_repo/1000/runs/1.json\n"
        "Writing a dict of 1 items to data/workflow_runs/my_repo/1000/runs/2.json\n"
        "Writing a list of 1 items to data/workflow_runs/my_repo/1000/pages/page_2.json\n"
        "Writing a dict of 1 items to data/workflow_runs/my_repo/1000/runs/3.json\n"
    )
