import collections
import os
import re

from .. import DATA_DIR, github_api, io


GITHUB_DIR = DATA_DIR / "github"
EARLY_DATE = "1970-01-01T00:00:00Z"


PR = collections.namedtuple(
    "PR",
    [
        "org",
        "repository",
        "number",
        "author",
        "created_at",
        "updated_at",
        "closed_at",
        "merged_at",
        "is_draft",
    ],
)


def main():  # pragma: no cover
    client = github_api.Client(
        {"opensafely-core": os.environ["GITHUB_OPENSAFELY_CORE_TOKEN"]}
    )
    get_prs(client, "opensafely-core", GITHUB_DIR / "opensafely-core" / "prs.csv")


def get_prs(client, org, file):
    """
    PRs are in a CSV file, ordered by update time (ascending).

    We update the local record by querying the GitHub API for PRs updated since the last fetch
    (determined by the update time of the last record in the file). We repeat this query until it
    doesn't yield any changes, which drains updates beyond the API's 1000-item search limit.

    If the local file is empty then we populate it from the beginning of history.

    PRs that are already in the local record but which have been updated since the last fetch are
    overwritten (and bumped to the end of the file).

    Note that the filter in the API query uses >=, not >. This is to handle the edge case where an
    update is made after a query returns but with the same (second-granularity) timestamp as the
    last record returned by the query. This means that we always return the last record of the
    previous query as the first record of the new one (or several records if we hit the
    same-timestamp edge case). These repeat updates are skipped.
    """
    old_prs = read_local_data(file)
    if old_prs:
        since = old_prs[-1].updated_at
    else:
        since = EARLY_DATE

    aggregate = {(pr.org, pr.repository, pr.number): pr for pr in old_prs}
    any_changes = False

    keep_going = True
    while keep_going:
        # Add new PRs and overwrite existing ones that have changed.
        batch_changes = False
        for pr in get_updates(client, org, since):
            key = (pr.org, pr.repository, pr.number)

            if key in aggregate and aggregate[key] == pr:
                # This PR has not changed, skip it. (See function comment above.) Assertion proves
                # that we really understand what's going on.
                assert pr.updated_at == since, (since, pr)
                continue

            if key in aggregate:
                # Dictionary insertion-order guarantee only holds for first insertion of a key, not
                # for overwrite by a new value. Remove the old value so that the update goes at the
                # end of the file.
                del aggregate[key]

            aggregate[key] = pr
            since = pr.updated_at
            batch_changes = True

        any_changes = any_changes or batch_changes
        keep_going = batch_changes

    if any_changes:
        tmp_file = file.with_suffix(".tmp.csv")
        io.write(aggregate.values(), tmp_file)
        tmp_file.replace(file)


def read_local_data(path):
    if not path.exists():
        return []

    try:
        return io.read(PR, path)
    except ValueError:
        # The fields in the file do not match our record type. This is probably because we've added
        # a new field. It's always safe to blow the data away and start again because it's just a
        # cache.
        path.unlink()
        return []


def get_updates(client, org, since):
    prs = client.query(org, github_api.PR_QUERY % (org, since))
    yield from (convert_pr(org, pr) for pr in prs)


def convert_pr(org, pr):
    def to_snake_case(name):
        # (?<!^) is a negative look-behind assertion to stop matches at the start of the string
        return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()

    def to_string(value):
        if value is None:
            return ""
        return str(value)

    flat = dict(pr)
    flat["repository"] = pr["repository"]["name"]  # flatten this nested structure
    flat["author"] = pr["author"]["login"]  # flatten
    flat["number"] = str(pr["number"])  # the API returns an integer

    snake = {to_snake_case(key): to_string(value) for key, value in flat.items()}
    snake["org"] = org

    # Check that the query and our record type are in sync
    assert set(snake.keys()) == set(PR._fields)

    return PR(**snake)


if __name__ == "__main__":
    main()
