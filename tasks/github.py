import os
import time

import requests


def get_token(org):
    env_vars = {
        "ebmdatalab": "GITHUB_EBMDATALAB_TOKEN",
        "bennettoxford": "GITHUB_BENNETTOXFORD_TOKEN",
        "opensafely-core": "GITHUB_OPENSAFELY_CORE_TOKEN",
        "opensafely": "GITHUB_OPENSAFELY_TOKEN",
    }
    return os.environ[env_vars[org]]


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


def fetch(org, first_page_url, *, results_key=None):
    url = first_page_url
    while True:
        response = get_with_retry(
            url,
            headers={"Authorization": f"Bearer {get_token(org)}"},
            params={"per_page": 100, "format": "json"},
        )
        page = response.json()
        records = page if results_key is None else page[results_key]
        yield from records
        if next_link := response.links.get("next"):
            url = next_link["url"]
        else:
            break


def fetch_repos(org):
    yield from fetch(org, f"https://api.github.com/orgs/{org}/repos")


def fetch_workflow_runs(org, repo_name):
    yield from fetch(
        org,
        f"https://api.github.com/repos/{org}/{repo_name}/actions/runs",
        results_key="workflow_runs",
    )


def fetch_prs(org, repo_name):
    yield from fetch(
        org, f"https://api.github.com/repos/{org}/{repo_name}/pulls?state=all"
    )
