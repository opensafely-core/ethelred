import collections

import pipeline
import sqlalchemy

from . import DATA_DIR, INDEX_DATE, io, utils


Record = collections.namedtuple("Record", ["repo", "sha", "project_definition"])


def extract(engine, metadata):
    job_request = metadata.tables["jobserver_jobrequest"]
    workspace = metadata.tables["jobserver_workspace"]
    repo = metadata.tables["jobserver_repo"]

    stmt = (
        sqlalchemy.select(
            repo.c.url,
            job_request.c.sha,
            job_request.c.project_definition,
        )
        .join(workspace, workspace.c.id == job_request.c.workspace_id)
        .join(repo, repo.c.id == workspace.c.repo_id)
        .where(job_request.c.created_at >= INDEX_DATE)
    )

    with engine.connect() as conn:
        yield from conn.execute(stmt)


def get_record(row):
    repo = utils.get_repo(row.url)
    project_definition = pipeline.loading.parse_yaml_file(row.project_definition)
    return Record(repo, row.sha, project_definition)


def write_pickle(records, project_definitions_dir):
    for record in records:
        f_path = project_definitions_dir / record.repo / f"{record.sha}.pickle"
        io.write(record.project_definition, f_path)


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine(utils.Database.JOBSERVER)
    metadata = utils.get_metadata(engine)

    rows = extract(engine, metadata)
    records = (get_record(row) for row in rows)
    write_pickle(records, DATA_DIR / "project_definitions")


if __name__ == "__main__":
    main()
