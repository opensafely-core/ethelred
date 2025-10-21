import datetime
import json
import pathlib
import types

import responses

from tasks import io
from tasks.tasks import get_workflow_runs


@responses.activate
def test_extract(tmpdir, monkeypatch):
    # Environment variable only needs to be available; correct usage tested in test_fetch_pages
    monkeypatch.setenv("GITHUB_TOKEN", "")

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
    assert io.read(output_dir / "runs" / "repo_1" / "20250101-000000" / "1.json") == {
        "id": 1
    }
    assert io.read(output_dir / "runs" / "repo_1" / "20250101-000000" / "2.json") == {
        "id": 2
    }


def test_filter_workflow_run_filepaths():
    older_dir = pathlib.Path("repo_1") / "20250101-000000"
    newer_dir = pathlib.Path("repo_1") / "20250102-000000"

    filepaths = [
        older_dir / "1.json",
        older_dir / "2.json",
        newer_dir / "2.json",
        newer_dir / "3.json",
    ]

    filtered = get_workflow_runs.filter_workflow_run_filepaths(filepaths)

    assert list(filtered) == [
        newer_dir / "3.json",
        newer_dir / "2.json",
        older_dir / "1.json",
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
def test_entrypoint(tmpdir, monkeypatch):
    # Environment variable only needs to be available; correct usage tested in test_fetch_pages
    monkeypatch.setenv("GITHUB_TOKEN", "")

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

    get_workflow_runs.entrypoint("test-org", workflows_dir, now_function=mock_now)

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
