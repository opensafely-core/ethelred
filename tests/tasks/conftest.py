import pytest


@pytest.fixture
def a_foreign_key():
    return 99


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
