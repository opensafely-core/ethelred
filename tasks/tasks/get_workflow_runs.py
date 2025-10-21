import collections
import datetime

from .. import DATA_DIR, github, io


Record = collections.namedtuple(
    "Record",
    [
        "id",
        "repo",
        "name",
        "head_sha",
        "status",
        "conclusion",
        "created_at",
        "updated_at",
        "run_started_at",
    ],
)


def extract(org, output_dir, datetime_):
    timestamp = datetime_.strftime("%Y%m%d-%H%M%S")
    for repo in github.fetch_repos(org):
        repo_name = repo["name"]
        io.write(repo, output_dir / "repos" / timestamp / f"{repo_name}.json")

        for run in github.fetch_workflow_runs(org, repo_name):
            io.write(
                run, output_dir / "runs" / repo_name / timestamp / f"{run['id']}.json"
            )


def filter_workflow_run_filepaths(filepaths):
    """
    Filters an iterable of filepaths to the latest retrieved file per workflow run.
    """
    filepaths = sorted(filepaths, reverse=True)
    seen = set()
    for filepath in filepaths:
        if filepath.name in seen:
            continue
        seen.add(filepath.name)
        yield filepath


def get_records(runs_dir):
    repos = (repo.name for repo in runs_dir.iterdir() if repo.is_dir())
    workflow_run_filepaths = [
        filepath
        for repo in repos
        for filepath in filter_workflow_run_filepaths(
            (runs_dir / repo).glob("*/*.json")
        )
    ]
    for filepath in workflow_run_filepaths:
        run = io.read(filepath)
        yield Record(
            id=run["id"],
            repo=run["repository"]["name"],
            name=run["name"],
            head_sha=run["head_sha"],
            status=run["status"],
            conclusion=run["conclusion"],
            created_at=run["created_at"],
            updated_at=run["updated_at"],
            run_started_at=run["run_started_at"],
        )


def entrypoint(org, workflows_dir, now_function=datetime.datetime.now):
    # Extract and write data to disk
    extract(org, workflows_dir, now_function(datetime.timezone.utc))
    # Get latest workflow runs from disk (may include past extractions)
    records = get_records(workflows_dir / "runs")
    # Load
    io.write(records, workflows_dir / "workflow_runs.csv")


def main():  # pragma: no cover
    entrypoint("opensafely", DATA_DIR / "workflow_runs")


if __name__ == "__main__":
    main()
