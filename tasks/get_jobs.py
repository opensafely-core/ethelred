import collections
import enum

import sqlalchemy

from . import DATA_DIR, INDEX_DATE, io, utils


Record = collections.namedtuple(
    "Record",
    [
        "id",
        "job_request_id",
        "created_at",
        "action_type",
        "status",
        "status_message_type",
    ],
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
        sqlalchemy.func.lower(job.c.status).label("status"),
        job.c.status_message,
    ).where(job.c.job_request_id.in_(subq))

    with engine.connect() as conn:
        yield from conn.execute(stmt)


def get_action(run_command):
    action, *_ = run_command.split()
    action_name, action_version = action.split(":")
    return action_name, action_version


class ActionType(enum.StrEnum):
    DATABASE = enum.auto()
    REUSABLE = enum.auto()
    SCRIPTED = enum.auto()
    OTHER = enum.auto()


_DATABASE_ACTIONS = {"cohortextractor", "ehrql"}

_REUSABLE_ACTIONS = {
    "cohort-joiner",
    "cohort-report",
    "cox-ipw",
    "dataset-report",
    "deciles-charts",
    "demographic-standardisation",
    "diabetes-algo",
    "kaplan-meier-function",
    "matching",
    "project-dag",
    "safetab",
}

_SCRIPTED_ACTIONS = {"python", "r", "stata"}


def get_action_type(action_name):
    if action_name in _DATABASE_ACTIONS:
        return ActionType.DATABASE

    if action_name in _REUSABLE_ACTIONS:
        return ActionType.REUSABLE

    if action_name in _SCRIPTED_ACTIONS:
        return ActionType.SCRIPTED

    return ActionType.OTHER


class StatusMessageType(enum.StrEnum):
    DEPENDENCY_FAILED = enum.auto()
    OTHER = enum.auto()


def get_status_message_type(status_message):
    match status_message:
        case "Not starting as dependency failed":
            return StatusMessageType.DEPENDENCY_FAILED
        case _:
            return StatusMessageType.OTHER


def get_records(rows):
    for row in rows:
        if row.run_command:
            action_name, _ = get_action(row.run_command)
        else:
            action_name = ""
        action_type = get_action_type(action_name)
        status_message_type = get_status_message_type(row.status_message)
        yield Record(
            row.id,
            row.job_request_id,
            row.created_at,
            action_type,
            row.status,
            status_message_type,
        )


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)
    rows = extract(engine, metadata)
    records = get_records(rows)
    io.write(records, DATA_DIR / "jobs" / "jobs.csv")


if __name__ == "__main__":
    main()
