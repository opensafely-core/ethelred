import functools
import os
import time

import requests

from . import io


REPOS_URL = "https://api.github.com/orgs/opensafely/repos"
WORKFLOW_RUNS_URL_TEMPLATE = (
    "https://api.github.com/repos/opensafely/{repo}/actions/runs"
)


def write_log(message):  # pragma: no cover
    # Placeholder: printing log messages to console for now.
    print(message)


class GitHubAPISession(requests.Session):
    def __init__(self, token=None):
        super().__init__()
        if token := os.environ.get("GITHUB_WORKFLOW_RUNS_TOKEN"):
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


def get_repo_names(session, output_dir):
    query_time = int(time.time())
    for page_number, response in enumerate(
        get_all_pages_with_retry(
            session.get, REPOS_URL, params={"format": "json", "per_page": 100}
        ),
        start=1,
    ):
        page = response.json()
        write_page(page, output_dir / str(query_time), page_number)
        yield from (repo["name"] for repo in page)


def write_workflow_runs(repo, session, output_dir):
    first_page_url = WORKFLOW_RUNS_URL_TEMPLATE.format(repo=repo)
    query_time = int(time.time())
    for page_number, response in enumerate(
        get_all_pages_with_retry(
            session.get, first_page_url, params={"format": "json", "per_page": 100}
        ),
        start=1,
    ):
        page = response.json()["workflow_runs"]
        write_page(page, output_dir / str(query_time), page_number)
        for run in page:
            write_run(run, output_dir / str(query_time))
