import collections
from pathlib import Path

import pytest

from tasks import io
from tasks.tasks import get_github_data
from tasks.tasks.get_github_data import PR


class FakeClient:
    def __init__(
        self,
        *batches,
        teams=None,
        team_repos=None,
        team_members=None,
    ):
        self._batches = list(batches)
        self.queries = []
        self._teams = teams
        self._team_repos = team_repos or {}
        self._team_members = team_members or {}

    def graphql_query(self, org, query):
        self.queries.append(query)
        if not self._batches:
            return []
        return self._batches.pop(0)

    def rest_query(self, path, **kwargs):
        if path.endswith("/teams"):
            if self._teams is not None:
                return [dict(slug=team) for team in self._teams]

            teams = sorted({*self._team_repos.keys(), *self._team_members.keys()})
            return [dict(slug=team) for team in teams]

        team = kwargs["team"]
        if path.endswith("/repos"):
            return [dict(name=repo) for repo in self._team_repos.get(team, [])]
        if path.endswith("/members"):
            return [dict(login=login) for login in self._team_members.get(team, [])]
        raise ValueError(path)


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


def test_fake_client_rest_query_raises_for_unexpected_path():
    client = FakeClient()
    with pytest.raises(ValueError):
        client.rest_query("/unexpected", team="team-rap")


def test_writes_team_members_with_team_membership_rows(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["team-rap", "team-rex", "tech-shared"],
        team_repos={"team-rap": ["repo-a"], "team-rex": [], "tech-shared": []},
        team_members={
            "team-rap": ["alice", "shared-user"],
            "team-rex": ["bob", "shared-user"],
            "tech-shared": ["carol"],
        },
    )

    get_github_data.get_teams(client, "org", root)

    rows = io.read(get_github_data.TEAM_MEMBER, root / "team_members.csv")
    assert rows == [
        get_github_data.TEAM_MEMBER("org", "team-rap", "alice"),
        get_github_data.TEAM_MEMBER("org", "team-rap", "shared-user"),
        get_github_data.TEAM_MEMBER("org", "team-rex", "bob"),
        get_github_data.TEAM_MEMBER("org", "team-rex", "shared-user"),
        get_github_data.TEAM_MEMBER("org", "tech-shared", "carol"),
    ]


def test_writes_team_repo_ownership(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["team-rap", "team-rex", "tech-shared"],
        team_repos={
            "team-rap": ["repo-a", "repo-b"],
            "team-rex": ["repo-c"],
            "tech-shared": [],
        },
        team_members={"team-rap": ["alice"], "team-rex": [], "tech-shared": []},
    )

    get_github_data.get_teams(client, "org", root)

    rows = io.read(get_github_data.TEAM_REPO, root / "team_repos.csv")
    assert rows == [
        get_github_data.TEAM_REPO("org", "team-rap", "repo-a"),
        get_github_data.TEAM_REPO("org", "team-rap", "repo-b"),
        get_github_data.TEAM_REPO("org", "team-rex", "repo-c"),
    ]


def test_fetches_all_teams_from_org_listing(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["platform", "research"],
        team_repos={"platform": ["repo-a"], "research": ["repo-b"]},
        team_members={"platform": ["alice"], "research": ["bob"]},
    )

    get_github_data.get_teams(client, "org", root)

    repos = io.read(get_github_data.TEAM_REPO, root / "team_repos.csv")
    members = io.read(get_github_data.TEAM_MEMBER, root / "team_members.csv")

    assert repos == [
        get_github_data.TEAM_REPO("org", "platform", "repo-a"),
        get_github_data.TEAM_REPO("org", "research", "repo-b"),
    ]
    assert members == [
        get_github_data.TEAM_MEMBER("org", "platform", "alice"),
        get_github_data.TEAM_MEMBER("org", "research", "bob"),
    ]


def test_preserves_duplicate_rows_if_returned_by_api(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["team-a"],
        team_repos={"team-a": ["repo-a", "repo-a"]},
        team_members={"team-a": ["shared", "shared"]},
    )

    get_github_data.get_teams(client, "org", root)

    repos = io.read(get_github_data.TEAM_REPO, root / "team_repos.csv")
    members = io.read(get_github_data.TEAM_MEMBER, root / "team_members.csv")

    assert repos == [
        get_github_data.TEAM_REPO("org", "team-a", "repo-a"),
        get_github_data.TEAM_REPO("org", "team-a", "repo-a"),
    ]
    assert members == [
        get_github_data.TEAM_MEMBER("org", "team-a", "shared"),
        get_github_data.TEAM_MEMBER("org", "team-a", "shared"),
    ]


def test_infers_team_list_when_teams_not_supplied(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        team_repos={"team-a": ["repo-a"]},
        team_members={"team-b": ["member-b"]},
    )

    get_github_data.get_teams(client, "org", root)

    repos = io.read(get_github_data.TEAM_REPO, root / "team_repos.csv")
    members = io.read(get_github_data.TEAM_MEMBER, root / "team_members.csv")

    assert repos == [get_github_data.TEAM_REPO("org", "team-a", "repo-a")]
    assert members == [get_github_data.TEAM_MEMBER("org", "team-b", "member-b")]


def test_preserves_team_iteration_order_from_api(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["z-team", "a-team"],
        team_repos={"z-team": ["repo-z"], "a-team": ["repo-a"]},
        team_members={"z-team": ["z-user"], "a-team": ["a-user"]},
    )

    get_github_data.get_teams(client, "org", root)

    repos = io.read(get_github_data.TEAM_REPO, root / "team_repos.csv")
    members = io.read(get_github_data.TEAM_MEMBER, root / "team_members.csv")

    assert repos == [
        get_github_data.TEAM_REPO("org", "z-team", "repo-z"),
        get_github_data.TEAM_REPO("org", "a-team", "repo-a"),
    ]
    assert members == [
        get_github_data.TEAM_MEMBER("org", "z-team", "z-user"),
        get_github_data.TEAM_MEMBER("org", "a-team", "a-user"),
    ]


def test_fails_fast_when_teams_have_no_metadata(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=["team-a"],
        team_repos={"team-a": []},
        team_members={"team-a": []},
    )

    with pytest.raises(StopIteration):
        get_github_data.get_teams(client, "org", root)


def test_fails_fast_when_metadata_is_empty(tmp_path):
    root = tmp_path / "org"
    client = FakeClient(
        teams=[],
        team_repos={},
        team_members={},
    )

    with pytest.raises(StopIteration):
        get_github_data.get_teams(client, "org", root)


def test_main_fetches_all_configured_orgs(tmp_path, monkeypatch):
    monkeypatch.setattr(get_github_data, "GITHUB_DIR", tmp_path)
    monkeypatch.setenv("GITHUB_OPENSAFELY_CORE_TOKEN", "core-token")
    monkeypatch.setenv("GITHUB_EBMDATALAB_TOKEN", "lab-token")
    monkeypatch.setenv("GITHUB_BENNETTOXFORD_TOKEN", "bennett-token")

    pr_calls = []
    team_calls = []

    class FakeMainClient:
        def __init__(self, tokens):
            self.tokens = tokens

    def fake_get_prs(client, org, file):
        pr_calls.append((org, file.relative_to(tmp_path)))

    def fake_get_teams(client, org, directory):
        team_calls.append((org, directory.relative_to(tmp_path)))

    monkeypatch.setattr(get_github_data.github_api, "Client", FakeMainClient)
    monkeypatch.setattr(get_github_data, "get_prs", fake_get_prs)
    monkeypatch.setattr(get_github_data, "get_teams", fake_get_teams)

    get_github_data.main()

    assert pr_calls == [
        ("opensafely-core", Path("opensafely-core/prs.csv")),
        ("ebmdatalab", Path("ebmdatalab/prs.csv")),
        ("bennettoxford", Path("bennettoxford/prs.csv")),
    ]
    assert team_calls == [
        ("opensafely-core", Path("opensafely-core")),
        ("ebmdatalab", Path("ebmdatalab")),
        ("bennettoxford", Path("bennettoxford")),
    ]


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
