import collections
import functools

import sqlalchemy

from . import DATA_DIR, INDEX_DATE, io, utils


Record = collections.namedtuple(
    "Record",
    [
        "created_at",
        "num_actions",
        "num_jobs",
        "username",
        "num_failed_jobs",
        "num_dependency_failed_jobs",
    ],
)


def extract(engine, metadata):
    job = metadata.tables["jobserver_job"]
    job_request = metadata.tables["jobserver_jobrequest"]
    workspace = metadata.tables["jobserver_workspace"]
    repo = metadata.tables["jobserver_repo"]
    user = metadata.tables["jobserver_user"]

    num_jobs_subq = (
        sqlalchemy.select(sqlalchemy.func.count(job.c.id))
        .where(job_request.c.id == job.c.job_request_id)
        .scalar_subquery()
    )
    num_failed_jobs_subq = (
        sqlalchemy.select(sqlalchemy.func.count(job.c.id))
        .where(job_request.c.id == job.c.job_request_id)
        .where(sqlalchemy.func.lower(job.c.status) == "failed")
        .scalar_subquery()
    )
    num_dependency_failed_jobs_subq = (
        sqlalchemy.select(sqlalchemy.func.count(job.c.id))
        .where(job_request.c.id == job.c.job_request_id)
        .where(job.c.status_message.ilike("Not starting as dependency failed"))
        .scalar_subquery()
    )
    stmt = (
        sqlalchemy.select(
            repo.c.url,
            job_request.c.sha,
            job_request.c.created_at,
            num_jobs_subq.label("num_jobs"),
            user.c.username,
            num_failed_jobs_subq.label("num_failed_jobs"),
            num_dependency_failed_jobs_subq.label("num_dependency_failed_jobs"),
        )
        .join(workspace, workspace.c.id == job_request.c.workspace_id)
        .join(repo, repo.c.id == workspace.c.repo_id)
        .join(user, user.c.id == job_request.c.created_by_id)
        .where(job_request.c.created_at >= INDEX_DATE)
    )

    with engine.connect() as conn:
        yield from conn.execute(stmt)


def load_project_definition(project_definitions_dir, repo, sha):
    return io.read(project_definitions_dir / repo / f"{sha}.pickle")


def get_records(rows, project_definition_loader):
    for row in rows:
        repo = utils.get_repo(row.url)
        project_definition = project_definition_loader(repo, row.sha)
        num_actions = len(project_definition["actions"])
        yield Record(
            row.created_at,
            num_actions,
            row.num_jobs,
            row.username,
            row.num_failed_jobs,
            row.num_dependency_failed_jobs,
        )


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)
    rows = extract(engine, metadata)

    project_definition_loader = functools.partial(
        load_project_definition, DATA_DIR / "project_definitions"
    )
    records = get_records(rows, project_definition_loader)

    io.write(records, DATA_DIR / "job_requests" / "job_requests.csv")


if __name__ == "__main__":
    main()
