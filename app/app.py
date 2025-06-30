import pathlib

import altair
import pandas
import streamlit


ROOT_DIR = pathlib.Path(__file__).parents[1]

DATA_DIR = ROOT_DIR / "data"


def get_job_requests(f_path):
    job_requests = pandas.read_csv(f_path)
    job_requests["measure"] = job_requests["num_jobs"] / job_requests["num_actions"]
    return job_requests


def get_histogram(job_requests, column_name):
    return (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(altair.X(column_name, bin=True), altair.Y("count()"))
    )


def get_scatter_plot(job_requests, column_names):
    encode_x, encode_y = column_names
    return altair.Chart(job_requests).mark_circle().encode(x=encode_x, y=encode_y)


def main():
    job_requests = get_job_requests(DATA_DIR / "job_requests" / "job_requests.csv")

    num_actions_histogram = get_histogram(job_requests, "num_actions")
    streamlit.write(num_actions_histogram)

    num_jobs_histogram = get_histogram(job_requests, "num_jobs")
    streamlit.write(num_jobs_histogram)

    measure_histogram = get_histogram(job_requests, "measure")
    streamlit.write(measure_histogram)

    scatter_plot = get_scatter_plot(job_requests, ("num_actions", "measure"))
    streamlit.write(scatter_plot)


if __name__ == "__main__":
    main()
