import collections

import sqlalchemy

from .. import DATA_DIR, db, io


Record = collections.namedtuple("Record", ["created_at", "id"])


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    codelists = metadata.tables["codelists_codelist"]
    stmt = sqlalchemy.select(codelists.c.created_at, codelists.c.id)
    with engine.connect() as conn:
        yield from conn.execute(stmt)


def get_records(rows):
    for row in rows:
        yield Record(row.created_at.replace(microsecond=0), row.id)


def main():  # pragma: no cover
    # This is hard to test without a OpenCodelists DB, so we exclude it from coverage.
    engine = db.get_engine(db.Database.OPENCODELISTS)
    metadata = db.reflect_metadata(engine)
    rows = extract(engine, metadata)

    records = get_records(rows)

    io.write(records, DATA_DIR / "opencodelists" / "codelist_create_events.csv")


if __name__ == "__main__":
    main()
