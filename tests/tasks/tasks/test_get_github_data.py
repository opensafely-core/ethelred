import collections

import pytest

from tasks import io
from tasks.tasks import get_github_data
from tasks.tasks.get_github_data import PR


class FakeClient:
    def __init__(self, *batches):
        self._batches = list(batches)
        self.queries = []

    def query(self, org, query):
        self.queries.append(query)
        if not self._batches:
            return []
        return self._batches.pop(0)


def test_writes_nothing_if_no_prs_returned(tmp_path):
    path, _ = run(tmp_path, prs=[])
    assert not path.exists()


def test_populate_initial_prs(tmp_path):
    path, _ = run(tmp_path, prs=[gh_pr(number=1)])
    prs = io.read(PR, path)
    assert prs == [local_pr(number=1)]


def test_append_new_prs(tmp_path):
    run(tmp_path, prs=[gh_pr(number=1)])
    path, _ = run(tmp_path, prs=[gh_pr(number=2)])
    prs = io.read(PR, path)
    assert prs == [local_pr(number=1), local_pr(number=2)]


def test_maintains_ordering_of_old_and_new_prs(tmp_path):
    run(tmp_path, prs=[gh_pr(number=1), gh_pr(number=2)])
    path, _ = run(tmp_path, prs=[gh_pr(number=3), gh_pr(number=4)])
    prs = io.read(PR, path)
    assert prs == [
        local_pr(number=1),
        local_pr(number=2),
        local_pr(number=3),
        local_pr(number=4),
    ]


def test_updated_pr(tmp_path):
    run(
        tmp_path,
        prs=[gh_pr(number=1, updated="2000-01-01T00:00:00Z"), gh_pr(number=2)],
    )

    # PR 1 has been updated
    path, _ = run(
        tmp_path,
        prs=[gh_pr(number=3), gh_pr(number=1, updated="2020-01-01T00:00:00Z")],
    )
    prs = io.read(PR, path)

    # PR 1 is moved to the end of the list and updated
    assert prs == [
        local_pr(number=2),
        local_pr(number=3),
        local_pr(number=1, updated="2020-01-01T00:00:00Z"),
    ]


def test_get_prs_repeats_until_no_changes(tmp_path):
    prs = [
        [gh_pr(number=1, updated="2000-01-01T00:00:00Z")],
        [
            gh_pr(number=1, updated="2000-01-01T00:00:00Z"),
            gh_pr(number=2, updated="2000-01-02T00:00:00Z"),
        ],
        [gh_pr(number=2, updated="2000-01-02T00:00:00Z")],
    ]

    _, client = run(tmp_path / "prs.csv", prs)

    assert len(client.queries) == 3
    assert "updated:>=2000-01-02T00:00:00Z" in client.queries[-1]


def test_filters_on_last_update_time(tmp_path):
    prs = [
        gh_pr(number=1, updated="2000-01-01T00:00:00Z"),
        gh_pr(number=2, updated="2001-01-01T00:00:00Z"),
    ]
    run(tmp_path, prs)

    _, client = run(tmp_path, prs=[])

    assert "updated:>=2001-01-01T00:00:00Z" in client.queries[-1]


def test_sort_by_update_time(tmp_path):
    _, client = run(tmp_path, prs=[])
    assert "sort:updated-asc" in client.queries[-1]


def test_schema_mismatch_deletes_cache(tmp_path):
    prs_path = tmp_path / "org" / "prs.csv"

    WrongType = collections.namedtuple("WrongType", ["aField"])
    io.write([WrongType("value")], prs_path)

    results = get_github_data.read_local_data(prs_path)

    assert not results
    assert not prs_path.exists()


def test_asserts_that_query_returns_expected_fields(tmp_path):
    pr = gh_pr()
    pr["newField"] = "value"
    with pytest.raises(AssertionError):
        run(tmp_path, [pr])


def local_pr(number=0, updated="1990-01-01T00:00:00Z"):
    return PR(
        "org",
        "repo",
        str(number),
        "author",
        "1990-01-01T00:00:00Z",
        updated,
        "",
        "",
        "False",
    )


def gh_pr(number=0, updated="1990-01-01T00:00:00Z"):
    return dict(
        repository=dict(name="repo"),
        number=number,
        author=dict(login="author"),
        createdAt="1990-01-01T00:00:00Z",
        updatedAt=updated,
        closedAt=None,
        mergedAt=None,
        isDraft=False,
    )


def run(root, prs):
    file = root / "prs.csv"
    if len(prs) == 0 or not isinstance(prs[0], list):
        prs = [prs]
    client = FakeClient(*prs)
    get_github_data.get_prs(client, "org", file)
    return file, client
