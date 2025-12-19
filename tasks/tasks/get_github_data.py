import collections
import os

from .. import DATA_DIR, github_api, io


PRS_DIR = DATA_DIR / "github" / "prs"
EARLY_DATE = "1970-01-01T00:00:00Z"


PR = collections.namedtuple(
    "PR",
    ["number", "author", "createdAt", "updatedAt", "closedAt", "mergedAt", "isDraft"],
)


def main():  # pragma: no cover
    client = github_api.Client(
        {"opensafely-core": os.environ["GITHUB_OPENSAFELY_CORE_TOKEN"]}
    )
    get_prs(client)


def get_prs(client):  # pragma: no cover
    for repo in ["job-server", "ethelred", "airlock", "job-runner"]:
        get_repo_prs(client, "opensafely-core", repo, PRS_DIR)


def get_repo_prs(client, org, repo, root):
    """
    PRs are stored per-repository in CSVs, ordered by update time (ascending).

    We incrementally update the local record by querying the GitHub API for PRs updated since the
    last fetch (determined by the update time of the last record in the file).

    If the local file is empty then we populate it from the beginning of history. This intial
    population is limited to roughly 1000 records (10 pages of results), to make development and
    testing easier. Repeated runs are needed for the population to complete for repositories with
    a lot of history.

    PRs that are already in the local record but which have been updated since the last fetch are
    overwritten (and bumped to the end of the file).

    Note that the filter in the API query uses >=, not >. This is to handle the edge case where an
    update is made after a query returns but with the same (second-granularity) timestamp as the
    last record returned by the query. This means that we always return the last record of the
    previous query as the first record of the new one, but that is harmless as it just results in a
    no-op overwrite of the previous record.
    """
    prs_file = root / org / repo / "prs.csv"

    old_prs = read_local_data(prs_file)
    if old_prs:
        since = old_prs[-1].createdAt
    else:
        since = EARLY_DATE

    new_prs = get_updates(client, org, repo, since)

    aggregate = {}
    for pr in old_prs:
        aggregate[pr.number] = pr

    # Add new PRs and overwrite existing ones that have changed.
    for pr in new_prs:
        if pr.number in aggregate:
            # Dictionary insertion-order guarantee only holds for first insertion of a key, not for
            # insertion of a new value. Remove the old value entirely so that the new record goes
            # at the end of the file.
            del aggregate[pr.number]
        aggregate[pr.number] = pr

    all_prs = aggregate.values()
    if not all_prs:
        return

    tmp_file = prs_file.with_suffix(".tmp.csv")
    io.write(all_prs, tmp_file)
    tmp_file.replace(prs_file)


def read_local_data(path):
    if not path.exists():
        return []

    return io.read(PR, path)


def get_updates(client, org, repo, since):
    prs = list(
        client.query(org, github_api.PR_QUERY % (org, repo, since), max_pages=10)
    )
    for pr in prs:
        pr["author"] = pr["author"]["login"]  # flatten this nested structure
        pr["number"] = str(pr["number"])  # bafflingly this is returned as an int

        yield PR(**pr)


if __name__ == "__main__":
    main()
