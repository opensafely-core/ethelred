import collections

from . import DATA_DIR, io, utils


Row = collections.namedtuple("Row", [])
Record = collections.namedtuple("Record", [])


def extract(engine, metadata):  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    yield from [Row()]


def transform(rows):
    for row in rows:
        yield Record()


def main():  # pragma: no cover
    # This is hard to test without a Job Server DB, so we exclude it from coverage.
    engine = utils.get_engine()
    metadata = utils.get_metadata(engine)
    rows = extract(engine, metadata)
    records = transform(rows)
    io.write(records, DATA_DIR / "jobs" / "jobs.csv")


if __name__ == "__main__":
    main()
