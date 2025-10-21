import collections
import datetime

from .. import DATA_DIR, github, io


Record = collections.namedtuple(
    "Record",
    [
        "id",
        "repo",
        "author",
        "created_at",
        "merged_at",
        "updated_at",
        "closed_at",
        "state",
        "draft",
    ],
)


def extract(org, output_dir, datetime_):
    timestamp = datetime_.strftime("%Y%m%d-%H%M%S")
    for repo in github.fetch_repos(org):
        repo_name = repo["name"]
        io.write(repo, output_dir / "repos" / timestamp / f"{repo_name}.json")

        for pr in github.fetch_prs(org, repo_name):
            io.write(
                pr, output_dir / "prs" / repo_name / timestamp / f"{pr['id']}.json"
            )


def filter_pr_filepaths(filepaths):
    """
    Filters an iterable of filepaths to the latest retrieved file per PR.
    """
    filepaths = sorted(filepaths, reverse=True)
    seen = set()
    for filepath in filepaths:
        if filepath.name in seen:
            continue
        seen.add(filepath.name)
        yield filepath


def get_records(prs_dir):
    repos = (repo.name for repo in prs_dir.iterdir() if repo.is_dir())
    pr_filepaths = [
        filepath
        for repo in repos
        for filepath in filter_pr_filepaths((prs_dir / repo).glob("*/*.json"))
    ]
    for filepath in pr_filepaths:
        pr = io.read(filepath)
        yield Record(
            id=pr["id"],
            repo=pr["base"]["repo"]["name"],
            author=pr["user"]["login"],
            created_at=pr["created_at"],
            merged_at=pr["merged_at"],
            updated_at=pr["updated_at"],
            closed_at=pr["closed_at"],
            state=pr["state"],
            draft=pr["draft"],
        )


def entrypoint(orgs, prs_dir, now_function=datetime.datetime.now):
    # Extract and write data to disk
    for org in orgs:
        extract(org, prs_dir, now_function(datetime.timezone.utc))
    # Get latest PRs from disk (may include past extractions)
    records = get_records(prs_dir / "prs")
    # Load
    io.write(records, prs_dir / "prs.csv")


def main():  # pragma: no cover
    entrypoint(
        ["opensafely", "opensafely-core", "ebmdatalab", "bennettoxford"],
        DATA_DIR / "prs",
    )


if __name__ == "__main__":
    main()
