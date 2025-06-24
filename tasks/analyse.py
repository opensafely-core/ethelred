import collections
import csv
import datetime

import altair

from . import DATA_DIR


def read_csv(f_path, transforms):
    with open(f_path, newline="") as f:
        reader = csv.reader(f)

        header = next(reader)
        assert len(transforms) == len(header)
        Record = collections.namedtuple("Record", header)

        rows = ((tr(value) for tr, value in zip(transforms, row)) for row in reader)
        records = (Record(*row) for row in rows)

        yield from records


def get_histogram(data):
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
    records = list(read_csv(DATA_DIR / "job_requests" / "job_requests.csv", transforms))

    d_path = DATA_DIR / "analysis"

    num_actions_histogram = get_histogram(r.num_actions for r in records)
    write(num_actions_histogram, d_path / "num_actions_histogram.png")

    num_jobs_histogram = get_histogram(r.num_jobs for r in records)
    write(num_jobs_histogram, d_path / "num_jobs_histogram.png")

    measure_histogram = get_histogram(r.num_jobs / r.num_actions for r in records)
    write(measure_histogram, d_path / "measure_histogram.png")


if __name__ == "__main__":
    main()
