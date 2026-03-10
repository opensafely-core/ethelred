from pathlib import Path

from delivery_metrics.repository import Repository, _uri_to_path


def test_load_prs_enriches_records(tmp_path):
    root = tmp_path / "data" / "github" / "opensafely-core"
    root.mkdir(parents=True)
    (root / "team_repos.csv").write_text(
        "org,team,repo\nopensafely-core,team-rap,reports\n"
    )
    (root / "team_members.csv").write_text(
        "org,team,login\nopensafely-core,team-rap,dev\n"
    )
    (root / "prs.csv").write_text(
        "org,repository,number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
        "opensafely-core,reports,1,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,2024-01-02T01:00:00Z,2024-01-02T01:00:00Z,False\n"
    )

    repository = Repository((tmp_path / "data").as_uri(), orgs=("opensafely-core",))
    [pr] = repository.load_prs()

    assert pr.repo.name == "reports"
    assert pr.is_content is False


def test_get_interesting_prs_excludes_bots_and_drafts(tmp_path):
    root = tmp_path / "data" / "github" / "opensafely-core"
    root.mkdir(parents=True)
    (root / "team_repos.csv").write_text(
        "org,team,repo\nopensafely-core,team-rap,reports\n"
    )
    (root / "team_members.csv").write_text(
        "org,team,login\nopensafely-core,team-rap,dev\n"
    )
    (root / "prs.csv").write_text(
        "org,repository,number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
        "opensafely-core,reports,1,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
        "opensafely-core,reports,2,dependabot,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
        "opensafely-core,reports,3,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,True\n"
    )

    repository = Repository((tmp_path / "data").as_uri(), orgs=("opensafely-core",))
    prs = repository.get_interesting_prs()

    assert len(prs) == 1
    assert prs[0].author == "dev"


def test_uri_to_path_handles_plain_paths():
    assert _uri_to_path("relative/path.csv") == Path("relative/path.csv")


def test_load_prs_includes_only_tech_owned_repos(tmp_path):
    root = tmp_path / "data" / "github" / "opensafely-core"
    root.mkdir(parents=True)
    (root / "team_repos.csv").write_text(
        "org,team,repo\nopensafely-core,team-rap,tech-repo\n"
    )
    (root / "team_members.csv").write_text(
        "org,team,login\nopensafely-core,team-rap,dev\n"
    )
    (root / "prs.csv").write_text(
        "org,repository,number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
        "opensafely-core,tech-repo,1,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
        "opensafely-core,other-repo,2,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
    )

    repository = Repository((tmp_path / "data").as_uri(), orgs=("opensafely-core",))
    prs = repository.load_prs()

    assert [pr.repo.name for pr in prs] == ["tech-repo"]


def test_load_prs_excludes_repos_owned_by_non_tech_teams(tmp_path):
    root = tmp_path / "data" / "github" / "opensafely-core"
    root.mkdir(parents=True)
    (root / "team_repos.csv").write_text(
        "org,team,repo\n"
        "opensafely-core,team-rap,tech-repo\n"
        "opensafely-core,other-team,non-tech-repo\n"
    )
    (root / "team_members.csv").write_text(
        "org,team,login\nopensafely-core,team-rap,dev\n"
    )
    (root / "prs.csv").write_text(
        "org,repository,number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
        "opensafely-core,tech-repo,1,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
        "opensafely-core,non-tech-repo,2,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
    )

    repository = Repository((tmp_path / "data").as_uri(), orgs=("opensafely-core",))
    prs = repository.load_prs()

    assert [pr.repo.name for pr in prs] == ["tech-repo"]


def test_load_prs_reads_all_default_orgs(tmp_path):
    root = tmp_path / "data" / "github"

    for org, repo in [
        ("opensafely-core", "core-repo"),
        ("ebmdatalab", "lab-repo"),
        ("bennettoxford", "bennett-repo"),
    ]:
        org_root = root / org
        org_root.mkdir(parents=True)
        (org_root / "team_repos.csv").write_text(
            f"org,team,repo\n{org},team-rap,{repo}\n"
        )
        (org_root / "team_members.csv").write_text(
            f"org,team,login\n{org},team-rap,dev\n"
        )
        (org_root / "prs.csv").write_text(
            "org,repository,number,author,created_at,updated_at,closed_at,merged_at,is_draft\n"
            f"{org},{repo},1,dev,2024-01-02T00:00:00Z,2024-01-02T00:00:00Z,,,False\n"
        )

    repository = Repository((tmp_path / "data").as_uri())
    prs = repository.load_prs()

    assert {(pr.repo.org, pr.repo.name) for pr in prs} == {
        ("opensafely-core", "core-repo"),
        ("ebmdatalab", "lab-repo"),
        ("bennettoxford", "bennett-repo"),
    }
