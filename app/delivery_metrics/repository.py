import csv
import datetime
from pathlib import Path
from urllib.parse import urlparse

from delivery_metrics import domain


DEFAULT_ORGS = ("opensafely-core", "ebmdatalab", "bennettoxford")
TECH_TEAMS = ("team-rap", "team-rex", "tech-shared")
MANAGERS = {"sebbacon", "benbc"}
EX_DEVELOPERS = {"ghickman", "milanwiedemann", "CarolineMorton"}
CONTENT_REPOS = {
    "ebmdatalab": {
        "opensafely.org",
        "team-manual",
        "bennett.ox.ac.uk",
        "openprescribing",
    }
}
EXCLUDED_AUTHORS = {"dependabot", "opensafely-core-create-pr"}


class Repository:
    def __init__(self, root_uri, orgs=DEFAULT_ORGS):
        self._root_uri = root_uri
        self._orgs = orgs

    def load_prs(self):
        team_members = set(MANAGERS) | set(EX_DEVELOPERS)
        tech_owned_repos = set()
        for org in self._orgs:
            org_dir = self._org_uri(org)
            tech_teams = self._tech_teams(org)
            tech_owned_repos.update(
                self._tech_owned_repos(org_dir / "team_repos.csv", tech_teams)
            )
            team_members.update(
                self._team_members(org_dir / "team_members.csv", tech_teams)
            )

        prs = []
        for org in self._orgs:
            for row in _read_csv(self._org_uri(org) / "prs.csv"):
                key = (row["org"], row["repository"])
                if key not in tech_owned_repos:
                    continue
                author = row["author"]
                repo = self._repo_for(row["org"], row["repository"])
                prs.append(
                    domain.PR(
                        repo=repo,
                        author=author,
                        created_at=_parse_datetime(row["created_at"]),
                        merged_at=_parse_datetime(row["merged_at"]),
                        closed_at=_parse_datetime(row["closed_at"]),
                        is_draft=_parse_bool(row["is_draft"]),
                        is_content=repo.is_content_repo and author not in team_members,
                    )
                )

        return prs

    def get_interesting_prs(self):
        return [
            pr
            for pr in self.load_prs()
            if pr.created_at.date() > domain.START_DATE
            and pr.author not in EXCLUDED_AUTHORS
            and not pr.is_draft
            and not pr.is_content
        ]

    def _org_uri(self, org):
        return _uri_to_path(f"{self._root_uri}/github/{org}")

    def _repo_for(self, org, name):
        content_repos = CONTENT_REPOS.get(org, set())
        return domain.Repo(org=org, name=name, is_content_repo=name in content_repos)

    def _tech_teams(self, org):
        return TECH_TEAMS

    def _tech_owned_repos(self, path, teams):
        return {
            (row["org"], row["repo"]) for row in _read_csv(path) if row["team"] in teams
        }

    def _team_members(self, path, teams):
        return {row["login"] for row in _read_csv(path) if row["team"] in teams}


def _read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def _uri_to_path(uri):
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(uri)


def _parse_datetime(value):
    if not value:
        return None
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_bool(value):
    return value == "True"
