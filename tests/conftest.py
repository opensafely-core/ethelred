import pytest
import sqlalchemy

from tasks import github

from .jobserver import tables


@pytest.fixture(scope="session")
def jobserver_engine():
    return sqlalchemy.create_engine("postgresql://user:pass@localhost:3979/jobserver")


@pytest.fixture
def jobserver_metadata(jobserver_engine):
    def return_false(*args, **kwargs):
        return False

    # Remove the foreign key constraints (but not the foreign keys) from the tables.
    # Doing so means we need only create the objects we wish to test, rather than these
    # objects and their dependants.
    for table in tables.metadata.sorted_tables:
        for foreign_key_constraint in table.foreign_key_constraints:
            foreign_key_constraint.ddl_if(callable_=return_false)

    tables.metadata.create_all(bind=jobserver_engine)
    yield tables.metadata
    tables.metadata.drop_all(bind=jobserver_engine)


@pytest.fixture
def stub_token(monkeypatch):
    monkeypatch.setattr(github, "get_token", lambda _: "a-token")
