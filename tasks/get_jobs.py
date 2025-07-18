import collections

import sqlalchemy

from . import DATA_DIR, INDEX_DATE, io, utils


Record = collections.namedtuple(
    "Record",
    ["id", "job_request_id", "created_at", "stage", "outcome"],
)


def extract(engine, metadata):
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
        stage = get_stage(row.run_command)
        outcome = get_outcome(row.status, row.status_message)
        yield Record(row.id, row.job_request_id, row.created_at, stage, outcome)


def get_stage(run_command):
    if not run_command:
        return ""
    action_name, _ = run_command.split(":", maxsplit=1)
    return "database" if action_name in {"cohortextractor", "ehrql"} else "analysis"


def get_outcome(status, status_message):
    match status:
        case "failed":
            match status_message.split(":")[0]:
                case "Not starting as dependency failed":
                    return "cancelled by dependency"
                case "Cancelled by user":
                    return "other"
                case (
                    "Job exited with an error"
                    | "Internal error"
                    | "No outputs found matching patterns"
                    | "GitRepoNotReachableError"
                ):
                    return "errored"
                case _:
                    return "other"
        case _:
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
