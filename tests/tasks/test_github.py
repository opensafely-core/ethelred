import types

import pytest
import responses
import responses.matchers

from tasks import github


@responses.activate
def test_get_with_retry_when_successful(capsys):
    def sleep(seconds):  # pragma: no cover
        # Should not be called but if this test fails,
        # we still don't want time.sleep to be called
        return

    responses.add(responses.GET, "http://test.url", json=["data_1", "data_2"])

    response = github.get_with_retry("http://test.url", sleep_function=sleep)
    assert response.json() == ["data_1", "data_2"]
    assert capsys.readouterr().out == ""


@responses.activate
def test_get_with_retry_when_fail(capsys):
    def sleep(seconds):
        return

    responses.add(responses.GET, "http://invalid.url", status=400)

    ERROR = "400 Client Error: Bad Request for url: http://invalid.url/"

    with pytest.raises(Exception, match=ERROR):
        github.get_with_retry("http://invalid.url", sleep_function=sleep)

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

    response = github.get_with_retry("http://flaky.url", sleep_function=sleep)

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
def test_fetch_with_top_level_results(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    match = [
        responses.matchers.header_matcher({"Authorization": "Bearer test_token"}),
        responses.matchers.query_param_matcher({"per_page": "100", "format": "json"}),
    ]
    responses.add(
        responses.GET,
        "https://test.url",
        json=[{"id": 1}],
        match=match,
        headers={"Link": '<https://nextpage.url>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://nextpage.url",
        json=[{"id": 2}],
        match=match,
    )

    records = github.fetch("https://test.url")

    assert isinstance(records, types.GeneratorType)
    assert list(records) == [{"id": 1}, {"id": 2}]


@responses.activate
def test_fetch_with_nested_results(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    responses.add(
        responses.GET,
        "https://test.url",
        json={"results": [{"id": 1}]},
    )

    records = github.fetch("https://test.url", results_key="results")
    assert list(records) == [{"id": 1}]


@responses.activate
def test_fetch_repos(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos?per_page=100&format=json",
        json=[{"id": 1}],
    )

    repos = github.fetch_repos("test-org")
    assert list(repos) == [{"id": 1}]


@responses.activate
def test_fetch_workflow_runs(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/test-repo/actions/runs?per_page=100&format=json",
        json={"workflow_runs": [{"id": 1}]},
    )

    repos = github.fetch_workflow_runs("test-org", "test-repo")
    assert list(repos) == [{"id": 1}]
