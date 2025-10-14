import collections
import datetime

import sqlalchemy

from .. import db, tables, utils


Record = collections.namedtuple("Record", ["login_at", "email_hash"])


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    users = metadata.tables["opencodelists_user"]
    stmt = sqlalchemy.select(users.c.last_login, users.c.email)
    with engine.connect() as conn:
        yield from conn.execute(stmt)


def get_records(rows):
    for row in rows:
        yield Record(
            row.last_login.replace(tzinfo=datetime.timezone.utc),
            utils.sha256(row.email),
        )


def main():  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    engine = db.get_engine(db.Database.OPENCODELISTS)
    metadata = db.get_metadata(engine)
    rows = (row for row in extract(engine, metadata) if row.last_login is not None)

    records = get_records(rows)

    db.write_records(
        records,
        db.get_engine(db.Database.ETHELRED),
        tables.opencodelists_logins,
    )


if __name__ == "__main__":
    main()
