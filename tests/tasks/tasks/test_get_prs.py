import datetime
import json
import pathlib
import types

import responses
import responses.matchers

from tasks import io
from tasks.tasks import get_prs


@responses.activate
def test_extract(tmpdir, stub_token):
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
        "https://api.github.com/repos/test-org/repo_1/pulls",
        json=[{"id": 1}],
        match=[
            responses.matchers.query_param_matcher({"state": "all"}, strict_match=False)
        ],
        headers={"Link": '<https://repo_1/prs.page2>; rel="next"'},
    )
    responses.add(
        responses.GET,
        "https://repo_1/prs.page2",
        json=[{"id": 2}],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/repo_2/pulls",
        json=[],
        match=[
            responses.matchers.query_param_matcher(
                {"state": "all", "per_page": 100, "format": "json"}
            )
        ],
    )

    output_dir = pathlib.Path(tmpdir)
    get_prs.extract("test-org", output_dir, datetime.datetime(2025, 1, 1))

    assert io.read(output_dir / "repos" / "20250101-000000" / "repo_1.json") == {
        "name": "repo_1"
    }
    assert io.read(output_dir / "repos" / "20250101-000000" / "repo_2.json") == {
        "name": "repo_2"
    }
    assert io.read(output_dir / "prs" / "repo_1" / "20250101-000000" / "1.json") == {
        "id": 1
    }
    assert io.read(output_dir / "prs" / "repo_1" / "20250101-000000" / "2.json") == {
        "id": 2
    }


def test_filter_pr_filepaths():
    older_dir = pathlib.Path("repo_1") / "20250101-000000"
    newer_dir = pathlib.Path("repo_1") / "20250102-000000"

    filepaths = [
        older_dir / "1.json",
        older_dir / "2.json",
        newer_dir / "2.json",
        newer_dir / "3.json",
    ]

    filtered = get_prs.filter_pr_filepaths(filepaths)

    assert list(filtered) == [
        newer_dir / "3.json",
        newer_dir / "2.json",
        older_dir / "1.json",
    ]


def test_get_records(tmpdir):
    template = {
        "id": None,  # Placeholder
        "state": "open",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "closed_at": "2025-01-01T00:00:00Z",
        "merged_at": "2025-01-01T00:00:00Z",
        "base": {"repo": {"name": None}},  # Placeholder
        "user": {"login": None},  # Placeholder
        "draft": False,
    }
    # Timestamp handling is tested elsewhere so only one timestamp per repo here
    prs_dir = pathlib.Path(tmpdir)
    repo_1_dir = prs_dir / "repo_1" / "20250101-000000"
    repo_2_dir = prs_dir / "repo_2" / "20250101-000000"
    repo_1_dir.mkdir(parents=True)
    repo_2_dir.mkdir(parents=True)

    repo_1_pr_1 = template | {
        "id": 1,
        "base": {"repo": {"name": "repo_1"}},
        "user": {"login": "author_1"},
    }
    (repo_1_dir / "1.json").write_text(json.dumps(repo_1_pr_1))
    repo_1_pr_2 = template | {
        "id": 2,
        "base": {"repo": {"name": "repo_1"}},
        "user": {"login": "author_2"},
    }
    (repo_1_dir / "2.json").write_text(json.dumps(repo_1_pr_2))
    repo_2_pr_3 = template | {
        "id": 3,
        "base": {"repo": {"name": "repo_2"}},
        "user": {"login": "author_3"},
    }
    (repo_2_dir / "3.json").write_text(json.dumps(repo_2_pr_3))

    records = get_prs.get_records(prs_dir)
    record_1, record_2, record_3 = sorted(records, key=lambda r: r.id)

    assert isinstance(records, types.GeneratorType)
    assert record_1._fields == get_prs.Record._fields
    assert record_1.id == 1
    assert record_1.repo == "repo_1"
    assert record_1.author == "author_1"
    assert record_2.id == 2
    assert record_2.repo == "repo_1"
    assert record_2.author == "author_2"
    assert record_3.id == 3
    assert record_3.repo == "repo_2"
    assert record_3.author == "author_3"


@responses.activate
def test_entrypoint(tmpdir, stub_token):
    # Run through pipeline for a single PR
    prs_dir = pathlib.Path(tmpdir)

    def mock_now(timezone):
        return datetime.datetime(2025, 1, 1, tzinfo=timezone)

    pr = {
        "id": 1,
        "state": "open",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "base": {"repo": {"name": "test_repo"}},
        "user": {"login": "test_author"},
        "draft": False,
    }

    responses.add(
        responses.GET,
        "https://api.github.com/orgs/test-org/repos",
        json=[{"name": "test_repo"}],
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/test-org/test_repo/pulls",
        json=[pr],
    )

    get_prs.entrypoint(["test-org"], prs_dir, now_function=mock_now)

    with open(prs_dir / "prs.csv") as f:
        csv_file = f.read()

    assert io.read(prs_dir / "repos" / "20250101-000000" / "test_repo.json") == {
        "name": "test_repo"
    }
    assert io.read(prs_dir / "prs" / "test_repo" / "20250101-000000" / "1.json") == pr
    assert csv_file == (
        "id,repo,author,created_at,merged_at,updated_at,closed_at,state,draft\n"
        "1,test_repo,test_author,2025-01-01T00:00:00Z,,2025-01-01T00:00:00Z,,open,False\n"
    )
