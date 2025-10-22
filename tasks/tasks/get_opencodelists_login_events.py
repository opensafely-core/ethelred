import collections

import sqlalchemy

from .. import DATA_DIR, db, io, utils


Record = collections.namedtuple("Record", ["login_at", "email_hash"])


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    users = metadata.tables["opencodelists_user"]
    stmt = sqlalchemy.select(users.c.last_login, users.c.email)
    with engine.connect() as conn:
        yield from conn.execute(stmt)


def get_records(rows):
    for row in rows:
        yield Record(row.last_login.replace(microsecond=0), utils.sha256(row.email))


def main():  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    engine = db.get_engine(db.Database.OPENCODELISTS)
    metadata = db.get_metadata(engine)
    rows = (row for row in extract(engine, metadata) if row.last_login is not None)

    records = get_records(rows)

    io.write(records, DATA_DIR / "opencodelists" / "login_events.csv")


if __name__ == "__main__":
    main()
