import collections
import functools
import os
import time

import requests

from . import DATA_DIR, io


REPOS_URL = "https://api.github.com/orgs/opensafely/repos"
WORKFLOW_RUNS_URL_TEMPLATE = (
    "https://api.github.com/repos/opensafely/{repo}/actions/runs"
)
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


def write_log(message):  # pragma: no cover
    # Placeholder: printing log messages to console for now.
    print(message)


class GitHubAPISession(requests.Session):
    def __init__(self, token=None):
        super().__init__()
        token = os.environ["GITHUB_WORKFLOW_RUNS_TOKEN"]
        self.headers.update({"Authorization": f"Bearer {token}"})


def retry(log, max_retries=3, backoff_seconds=0.5):
    def decorator(get):
        @functools.wraps(get)
        def wrapper(url, **kwargs):
            retry_count = 0
            while True:
                try:
                    response = get(url, **kwargs)
                    response.raise_for_status()
                    return response
                except requests.RequestException as error:
                    if retry_count < max_retries:
                        seconds = backoff_seconds * (2**retry_count)
                        log(
                            f"Error fetching {url}: {error}\n"
                            f"Retrying in {seconds} seconds (retry attempt {retry_count + 1}) ..."
                        )
                        time.sleep(seconds)
                        retry_count += 1
                    else:
                        log(
                            f"Error fetching {url}: {error}\n"
                            f"Maximum retries reached ({max_retries})."
                        )
                        return response

        return wrapper

    return decorator


def write_page(page, output_dir, page_number):
    filename = output_dir / "pages" / f"page_{page_number}.json"
    io.write(page, filename)


def write_run(run, output_dir):
    filename = output_dir / "runs" / f"{run['id']}.json"
    io.write(run, filename)


def get_all_pages_with_retry(get_function, first_url, **kwargs):
    url = first_url
    while True:
        response = retry(write_log)(get_function)(url, **kwargs)
        if response.status_code != 200:
            write_log("Skipping.")
            break  # give up as we have already retried
        yield response
        if next_link := response.links.get("next"):
            url = next_link["url"]
        else:
            break


def get_repos_pages(session):
    yield from (
        response.json()
        for response in get_all_pages_with_retry(
            session.get, REPOS_URL, params={"format": "json", "per_page": 100}
        )
    )


def get_workflow_runs_pages(repo, session):
    first_page_url = WORKFLOW_RUNS_URL_TEMPLATE.format(repo=repo)
    yield from (
        response.json()["workflow_runs"]
        for response in get_all_pages_with_retry(
            session.get, first_page_url, params={"format": "json", "per_page": 100}
        )
    )


def get_latest_run_filepaths(repo_dir):
    files = {}
    timestamps = [int(d.name) for d in repo_dir.iterdir() if d.is_dir()]
    for timestamp in sorted(timestamps, reverse=True):
        if not (runs_dir := repo_dir / str(timestamp) / "runs").exists():
            continue
        dir_files = {
            file_path.name: file_path
            for file_path in runs_dir.iterdir()
            if file_path.suffix == ".json"
        }
        files = dir_files | files  # keep the most recent files
    return [files[filename] for filename in sorted(files.keys())]


def get_record(run):
    return Record(
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


def main(session, workflows_dir):
    # Use the same timestamp to name all directories in this extraction
    timestamp = int(time.time())
    repos_pages = get_repos_pages(session)
    repo_names = []
    for page_number, repos_page in enumerate(repos_pages, start=1):
        write_page(repos_page, workflows_dir / "repos" / str(timestamp), page_number)
        for repo in (repo["name"] for repo in repos_page):
            runs_pages = get_workflow_runs_pages(repo, session)
            for page_number, runs_page in enumerate(runs_pages, start=1):
                write_page(
                    runs_page, workflows_dir / repo / str(timestamp), page_number
                )
                for run in runs_page:
                    write_run(run, workflows_dir / repo / str(timestamp))
            repo_names.append(repo)

    filepaths = [
        filepath
        for filepaths in [
            get_latest_run_filepaths(workflows_dir / repo) for repo in repo_names
        ]
        for filepath in filepaths
    ]
    records = (get_record(io.read(filepath)) for filepath in filepaths)
    io.write(records, workflows_dir / "workflow_runs.csv")


if __name__ == "__main__":
    session = GitHubAPISession()
    main(session, DATA_DIR / "workflow_runs")
