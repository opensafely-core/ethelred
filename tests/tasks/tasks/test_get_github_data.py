from tasks import io
from tasks.tasks.get_github_data import PR, get_repo_prs


class FakeClient:
    def __init__(self, records):
        self._records = records

    def query(self, org, query, max_pages):
        return self._records


def test_writes_nothing_if_no_data_returned(tmp_path):
    path = run([], tmp_path)
    assert not path.exists()


def test_populate_initial_prs(tmp_path):
    path = run([gh_pr(number=1)], tmp_path)
    prs = io.read(PR, path)
    assert prs == [local_pr(number=1)]


def test_append_new_prs(tmp_path):
    run([gh_pr(number=1)], tmp_path)
    path = run([gh_pr(number=2)], tmp_path)
    prs = io.read(PR, path)
    assert prs == [local_pr(number=1), local_pr(number=2)]


def test_maintains_ordering_of_old_and_new_prs(tmp_path):
    run([gh_pr(number=1), gh_pr(number=2)], tmp_path)
    path = run([gh_pr(number=3), gh_pr(number=4)], tmp_path)
    prs = io.read(PR, path)
    assert prs == [
        local_pr(number=1),
        local_pr(number=2),
        local_pr(number=3),
        local_pr(number=4),
    ]


def test_updated_pr(tmp_path):
    run([gh_pr(number=1, updated="2000-01-01T00:00:00Z"), gh_pr(number=2)], tmp_path)

    # PR 1 has been updated
    path = run(
        [gh_pr(number=3), gh_pr(number=1, updated="2020-01-01T00:00:00Z")], tmp_path
    )
    prs = io.read(PR, path)

    # PR 1 is moved to the end of the list and updated
    assert prs == [
        local_pr(number=2),
        local_pr(number=3),
        local_pr(number=1, updated="2020-01-01T00:00:00Z"),
    ]


def local_pr(number=0, updated=""):
    return PR(str(number), "author", "1990-01-01T00:00:00Z", updated, "", "", "False")


def gh_pr(number=0, updated=None):
    return dict(
        number=number,
        author=dict(login="author"),
        createdAt="1990-01-01T00:00:00Z",
        updatedAt=updated,
        closedAt=None,
        mergedAt=None,
        isDraft=False,
    )


def run(prs, root):
    get_repo_prs(FakeClient(prs), "org", "repo", root)
    return root / "org" / "repo" / "prs.csv"
