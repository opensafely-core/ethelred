import collections
import pickle

import pipeline
import sqlalchemy

from . import DATA_DIR, INDEX_DATE, utils


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


def write(record):
    d_path = DATA_DIR / "project_definitions" / record.repo
    d_path.mkdir(parents=True, exist_ok=True)

    f_path = d_path / f"{record.sha}.pickle"
    with f_path.open("wb") as f:
        pickle.dump(record.project_definition, f)


def main():
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)

    rows = extract(engine, metadata)
    records = (record for row in rows if (record := get_record(row)) is not None)
    for record in records:
        write(record)


if __name__ == "__main__":
    main()
