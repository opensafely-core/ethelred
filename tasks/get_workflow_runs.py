import collections
import datetime
import os
import time

import requests

from . import DATA_DIR, io


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


def get_token():
    return os.environ["GITHUB_WORKFLOW_RUNS_TOKEN"]


def get_with_retry(
    url,
    headers=None,
    params=None,
    max_retries=3,
    base_delay_seconds=0.5,
    sleep_function=time.sleep,
):
    retry_count = 0
    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        except Exception as error:
            print(f"Error fetching {url}: {error}")
            if retry_count < max_retries:
                delay_seconds = base_delay_seconds * (2**retry_count)
                print(
                    f"Retrying in {delay_seconds} seconds (retry attempt {retry_count + 1})..."
                )
                retry_count += 1
                sleep_function(delay_seconds)
            else:
                print(f"Maximum retries reached ({max_retries}).")
                raise


def fetch_pages(first_page_url):
    url = first_page_url
    while True:
        response = get_with_retry(
            url,
            headers={"Authorization": f"Bearer {get_token()}"},
            params={"per_page": 100, "format": "json"},
        )
        yield response.json()
        if next_link := response.links.get("next"):
            url = next_link["url"]
        else:
            break


def fetch_repos(org):
    for page in fetch_pages(f"https://api.github.com/orgs/{org}/repos"):
        yield from page


def fetch_workflow_runs_for_repo(org, repo_name):
    for page in fetch_pages(
        f"https://api.github.com/repos/{org}/{repo_name}/actions/runs"
    ):
        yield from page["workflow_runs"]


def extract(org, output_dir, datetime_):
    timestamp = datetime_.strftime("%Y%m%d-%H%M%S")
    for repo in fetch_repos(org):
        repo_name = repo["name"]
        io.write(repo, output_dir / "repos" / timestamp / f"{repo_name}.json")

        runs = fetch_workflow_runs_for_repo(org, repo_name)
        for run in runs:
            io.write(
                run, output_dir / "runs" / repo_name / timestamp / f"{run['id']}.json"
            )


def get_names_of_extracted_repos(runs_dir):
    # Being deterministic is more important than saving memory for a couple of strings
    return sorted(repo.name for repo in runs_dir.iterdir() if repo.is_dir())


def load_latest_workflow_runs(repo_dir):
    filepaths = sorted(repo_dir.glob("*/*.json"), reverse=True)
    seen = set()
    for filepath in filepaths:
        if filepath.name in seen:
            continue
        seen.add(filepath.name)
        yield io.read(filepath)


def get_records(runs_dir):
    repos = get_names_of_extracted_repos(runs_dir)
    workflow_runs = (
        run for repo in repos for run in load_latest_workflow_runs(runs_dir / repo)
    )
    for run in workflow_runs:
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


def main(org, workflows_dir, now_function=datetime.datetime.now):
    # Extract and write data to disk
    extract(org, workflows_dir, now_function(datetime.timezone.utc))
    # Get latest workflow runs from disk (may include past extractions)
    records = get_records(workflows_dir / "runs")
    # Load
    io.write(records, workflows_dir / "workflow_runs.csv")


if __name__ == "__main__":
    main("opensafely", DATA_DIR / "workflow_runs")
