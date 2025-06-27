import collections
import csv
import functools
import itertools
import pickle

import sqlalchemy

from . import DATA_DIR, INDEX_DATE, utils


Record = collections.namedtuple("Record", ["created_at", "num_actions", "num_jobs"])


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    job = metadata.tables["jobserver_job"]
    job_request = metadata.tables["jobserver_jobrequest"]
    workspace = metadata.tables["jobserver_workspace"]
    repo = metadata.tables["jobserver_repo"]

    subq = (
        sqlalchemy.select(sqlalchemy.func.count(job.c.id))
        .where(job_request.c.id == job.c.job_request_id)
        .scalar_subquery()
    )
    stmt = (
        sqlalchemy.select(
            repo.c.url,
            job_request.c.sha,
            job_request.c.created_at,
            subq.label("num_jobs"),
        )
        .join(workspace, workspace.c.id == job_request.c.workspace_id)
        .join(repo, repo.c.id == workspace.c.repo_id)
        .where(job_request.c.created_at >= INDEX_DATE)
    )

    with engine.connect() as conn:
        yield from conn.execute(stmt)


def load_project_definition(project_definitions_dir, repo, sha):
    f_path = project_definitions_dir / repo / f"{sha}.pickle"
    with f_path.open("rb") as f:
        return pickle.load(f)


def get_record(row, project_definition):
    num_actions = len(project_definition["actions"])
    return Record(row.created_at, num_actions, row.num_jobs)


def transform(rows, project_definition_loader):
    for row in rows:
        repo = utils.get_repo(row.url)
        project_definition = project_definition_loader(repo, row.sha)
        yield get_record(row, project_definition)


def write_csv(records, f_path):
    records = iter(records)
    record_0 = next(records)
    f_path.parent.mkdir(parents=True, exist_ok=True)
    with f_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(itertools.chain([record_0._fields], [record_0], records))


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)
    rows = extract(engine, metadata)

    project_definition_loader = functools.partial(
        load_project_definition, DATA_DIR / "project_definitions"
    )
    records = transform(rows, project_definition_loader)

    write_csv(records, DATA_DIR / "job_requests" / "job_requests.csv")


if __name__ == "__main__":
    main()
