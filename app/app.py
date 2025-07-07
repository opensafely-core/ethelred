import os
import pathlib

import altair
import pandas
import streamlit


DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "data"))


def get_job_requests(f_path):
    job_requests = pandas.read_csv(f_path)
    job_requests["measure"] = job_requests["num_jobs"] / job_requests["num_actions"]
    return job_requests


def get_jobs(f_path):
    jobs = pandas.read_csv(f_path)
    return jobs


def calculate_proportions(jobs):
    """
    Returns a one row per job request DataFrame with a single column "proportion"
    that contains the proportion of jobs cancelled by dependency out of all
    jobs that either errored or were cancelled by dependency.

    Job requests with no jobs that errored or were cancelled by dependency
    are filtered out.
    """
    job_requests = (
        jobs.groupby(["job_request_id", "outcome"])
        .size()
        .unstack(fill_value=0)
        .add_prefix("num_")
    )
    job_requests["denominator"] = (
        job_requests["num_errored"] + job_requests["num_cancelled by dependency"]
    )
    job_requests = job_requests.loc[job_requests["denominator"] > 0]
    job_requests["proportion"] = (
        job_requests["num_cancelled by dependency"] / job_requests["denominator"]
    )
    return job_requests.loc[:, "proportion"].to_frame()


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
    jobs = get_jobs(DATA_DIR / "jobs" / "jobs.csv")

    num_actions_histogram = get_histogram(job_requests, "num_actions")
    streamlit.write(num_actions_histogram)

    num_jobs_histogram = get_histogram(job_requests, "num_jobs")
    streamlit.write(num_jobs_histogram)

    measure_histogram = get_histogram(job_requests, "measure")
    streamlit.write(measure_histogram)

    proportion_histogram = get_histogram(calculate_proportions(jobs), "proportion")
    streamlit.write(proportion_histogram)

    scatter_plot = get_scatter_plot(job_requests, ("num_actions", "measure"))
    streamlit.write(scatter_plot)


if __name__ == "__main__":
    main()
