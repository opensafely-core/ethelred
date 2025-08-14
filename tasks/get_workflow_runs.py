import collections
import datetime
import itertools
import json
import os
import time

import requests

from . import DATA_DIR, io


GITHUB_ORG = "opensafely"

File = collections.namedtuple("File", ["filepath", "text"])
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


class GitHubAPISession(requests.Session):
    def __init__(self, token=None):
        super().__init__()
        token = os.environ["GITHUB_WORKFLOW_RUNS_TOKEN"]
        self.headers.update({"Authorization": f"Bearer {token}"})
        self.params.update({"per_page": 100, "format": "json"})


class SessionWithRetry:
    def __init__(
        self, session, max_retries=3, base_delay_seconds=0.5, sleep_function=time.sleep
    ):
        self.session = session
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.sleep = sleep_function

    def get(self, url):
        retry_count = 0
        while True:
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response
            except Exception as error:
                print(f"Error fetching {url}: {error}")
                if retry_count < self.max_retries:
                    delay_seconds = self.base_delay_seconds * (2**retry_count)
                    print(
                        f"Retrying in {delay_seconds} seconds (retry attempt {retry_count + 1})..."
                    )
                    retry_count += 1
                    self.sleep(delay_seconds)
                else:
                    print(f"Maximum retries reached ({self.max_retries}).")
                    return response


def get_pages(session, first_page_url):
    url = first_page_url
    while True:
        response = session.get(url)
        yield response
        if next_link := response.links.get("next"):
            url = next_link["url"]
        else:
            break


def _extract_repo_names_from_pages(repos_pages):
    decoded_pages = (page.json() for page in repos_pages)
    return (repo["name"] for page in decoded_pages for repo in page)


def get_repo_names(session):
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos"
    pages_1, pages_2 = itertools.tee(get_pages(session, url))
    return pages_1, _extract_repo_names_from_pages(pages_2)


def _extract_workflow_runs_from_pages(workflow_runs_pages):
    decoded_pages = (page.json() for page in workflow_runs_pages)
    return (run for page in decoded_pages for run in page["workflow_runs"])


def get_repo_workflow_runs(repo_name, session):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/actions/runs"
    pages_1, pages_2 = itertools.tee(get_pages(session, url))
    return pages_1, _extract_workflow_runs_from_pages(pages_2)


def get_page_files(pages, output_dir):
    for page_number, page in enumerate(pages, start=1):
        yield File(output_dir / "pages" / f"{page_number}.json", page.text)


def get_run_files(workflow_runs, output_dir):
    for run in workflow_runs:
        yield File(output_dir / "runs" / f"{run['id']}.json", json.dumps(run))


def extract(session, output_dir, datetime_, write_function):
    timestamp = datetime_.strftime("%Y%m%d-%H%M%SZ")
    repo_pages, repo_names = get_repo_names(session)
    repo_files = get_page_files(repo_pages, output_dir / "repos" / timestamp)

    file_iterables = [repo_files]
    for repo_name in repo_names:
        run_pages, runs = get_repo_workflow_runs(repo_name, session)
        page_files = get_page_files(run_pages, output_dir / repo_name / timestamp)
        run_files = get_run_files(runs, output_dir / repo_name / timestamp)
        file_iterables.extend([page_files, run_files])

    for file in itertools.chain(*file_iterables):
        write_function(file.text, file.filepath)


def get_names_of_extracted_repos(workflows_dir):
    # Being deterministic is more important than saving memory for a couple of strings
    return sorted(repo.name for repo in workflows_dir.iterdir() if repo.is_dir())


def load_latest_workflow_runs(repo_dir):
    filepaths = sorted(repo_dir.glob("*/runs/*.json"), reverse=True)
    seen = set()
    for filepath in filepaths:
        if filepath.name in seen:
            continue
        seen.add(filepath.name)
        with filepath.open() as f:
            yield json.load(f)


def get_records(workflows_dir):
    repos = get_names_of_extracted_repos(workflows_dir)
    workflow_runs = (
        run for repo in repos for run in load_latest_workflow_runs(workflows_dir / repo)
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


def main(session, workflows_dir, now_function=datetime.datetime.now):
    # Extract and write data to disk
    extract(SessionWithRetry(session), workflows_dir, now_function(), io.write)
    # Get latest workflow runs from disk (may include past extractions)
    records = get_records(workflows_dir)
    # Load
    io.write(records, workflows_dir / "workflow_runs.csv")


if __name__ == "__main__":
    session = GitHubAPISession()
    main(session, DATA_DIR / "workflow_runs")
