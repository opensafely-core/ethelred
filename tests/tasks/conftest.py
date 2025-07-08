import pytest


@pytest.fixture
def a_foreign_key():
    return 99


@pytest.fixture
def example_repo():
    return {
        "id": 1,
        "url": "https://github.com/opensafely/my-repo",
        "has_github_outputs": False,
    }


@pytest.fixture
def example_workspace(a_foreign_key, example_repo):
    return {
        "id": 1,
        "created_by_id": a_foreign_key,
        "project_id": a_foreign_key,
        "uses_new_release_flow": True,
        "repo_id": example_repo["id"],
        "signed_off_by_id": a_foreign_key,
        "purpose": "a purpose",
        "updated_at": "1900-01-01T00:00:00Z",
        "updated_by_id": a_foreign_key,
    }


@pytest.fixture
def example_user(a_foreign_key):
    return {
        "id": 1,
        "username": "my-username",
        "created_by_id": a_foreign_key,
        "fullname": "Some User",
        "roles": ["some role"],
    }


@pytest.fixture
def make_jobrequest(a_foreign_key):
    def _make_jobrequest(id_, created_at, **kwargs):
        return {
            "id": id_,
            "created_at": created_at,
            "backend_id": a_foreign_key,
            "created_by_id": a_foreign_key,
            "workspace_id": a_foreign_key,
            "requested_actions": ["a1"],
            "project_definition": "actions: {a1: {}, a2: {}}",
            "codelists_ok": True,
        } | kwargs

    return _make_jobrequest


@pytest.fixture
def make_job():
    def _make_job(id_, job_request_id, created_at):
        return {
            "id": id_,
            "job_request_id": job_request_id,
            "created_at": created_at,
            "action": "do_something",
            "run_command": "command:version some_script.py",
            "status": "some status",
            "status_code": "000",
            "status_message": "some status message",
        }

    return _make_job
