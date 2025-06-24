import collections
import csv
import datetime

import altair

from . import DATA_DIR


def extract(f_path, transforms):
    with f_path.open(newline="") as f:
        reader = csv.reader(f)

        header = next(reader)
        assert len(transforms) == len(header)
        Record = collections.namedtuple("Record", header)

        rows = ((tr(value) for tr, value in zip(transforms, row)) for row in reader)
        records = (Record(*row) for row in rows)

        yield from records


def transform(data):
    return (
        altair.Chart(altair.InlineData(list(data)))
        .mark_bar()
        .encode(altair.X("data:Q", bin=True), altair.Y("count()"))
    )


def write(chart, f_path):
    f_path.parent.mkdir(parents=True, exist_ok=True)
    chart.save(f_path)


def main():
    transforms = (datetime.datetime.fromisoformat, int, int)
    records = list(extract(DATA_DIR / "job_requests" / "job_requests.csv", transforms))

    d_path = DATA_DIR / "analysis"

    num_actions_histogram = transform(r.num_actions for r in records)
    write(num_actions_histogram, d_path / "num_actions_histogram.png")

    num_jobs_histogram = transform(r.num_jobs for r in records)
    write(num_jobs_histogram, d_path / "num_jobs_histogram.png")

    measure_histogram = transform(r.num_jobs / r.num_actions for r in records)
    write(measure_histogram, d_path / "measure_histogram.png")


if __name__ == "__main__":
    main()
