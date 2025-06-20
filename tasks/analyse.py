import csv
import datetime
import functools

import altair

from . import DATA_DIR


to_datetime = functools.partial(map, datetime.datetime.fromisoformat)
to_int = functools.partial(map, int)


def extract():
    f_path = DATA_DIR / "job_requests" / "job_requests.csv"
    with f_path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)  # discard the header

        transforms = (to_datetime, to_int, to_int)
        columns = zip(*reader)
        return tuple(list(tr(col)) for tr, col in zip(transforms, columns, strict=True))


def get_measure(num_actions, num_jobs):
    return [j / a for a, j in zip(num_actions, num_jobs)]


def transform(data):
    return (
        altair.Chart(altair.InlineData(data))
        .mark_bar()
        .encode(altair.X("data:Q", bin=True), altair.Y("count()"))
    )


def write(chart, f_name):
    d_path = DATA_DIR / "analysis"
    d_path.mkdir(parents=True, exist_ok=True)
    chart.save(d_path / f_name)


def main():
    _, num_actions, num_jobs = extract()
    measure = get_measure(num_actions, num_jobs)

    num_actions_histogram = transform(num_actions)
    write(num_actions_histogram, "num_actions_histogram.png")

    num_jobs_histogram = transform(num_jobs)
    write(num_jobs_histogram, "num_jobs_histogram.png")

    measure_histogram = transform(measure)
    write(measure_histogram, "measure_histogram.png")


if __name__ == "__main__":
    main()
