import collections

import sqlalchemy

from . import DATA_DIR, INDEX_DATE, io, utils


Record = collections.namedtuple(
    "Record",
    ["id", "job_request_id", "created_at", "stage", "outcome"],
)


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    job = metadata.tables["jobserver_job"]
    job_request = metadata.tables["jobserver_jobrequest"]

    subq = sqlalchemy.select(job_request.c.id).where(
        job_request.c.created_at >= INDEX_DATE
    )
    stmt = sqlalchemy.select(
        job.c.id,
        job.c.job_request_id,
        job.c.created_at,
        job.c.run_command,
        job.c.status,
        job.c.status_message,
    ).where(job.c.job_request_id.in_(subq))

    with engine.connect() as conn:
        yield from conn.execute(stmt)


def transform(rows):
    for row in rows:
        yield Record(
            row.id,
            row.job_request_id,
            row.created_at,
            get_stage(row.run_command),
            get_outcome(row.status, row.status_message),
        )


def get_stage(run_command):
    database_commands = ["ehrql"]
    if run_command.split(":")[0] in database_commands:
        return "database"
    return "analysis"


def get_outcome(status, status_message):
    if status == "failed":
        if status_message.startswith("Not starting as dependency failed"):
            return "cancelled by dependency"
        elif (
            status_message.startswith("Job exited with an error")
            or status_message.startswith("Internal error")
            or status_message.startswith("No outputs found matching patterns")
            or status_message.startswith("GitRepoNotReachableError")
        ):
            return "errored"
    return "other"


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)
    rows = extract(engine, metadata)
    records = transform(rows)
    io.write(records, DATA_DIR / "jobs" / "jobs.csv")


if __name__ == "__main__":
    main()
