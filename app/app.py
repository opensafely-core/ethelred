import os
import pathlib
from enum import Enum

import altair
import pandas
import streamlit


DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "data"))

Outcome = Enum("Outcome", ["CANCELLED_BY_DEPENDENCY", "ERRORED", "OTHER"])


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
        .rename(columns={outcome.value: f"num_{outcome}" for outcome in Outcome})
    )
    job_requests["denominator"] = (
        job_requests[f"num_{Outcome.ERRORED}"]
        + job_requests[f"num_{Outcome.CANCELLED_BY_DEPENDENCY}"]
    )
    job_requests = job_requests.loc[job_requests["denominator"] > 0]
    job_requests["proportion"] = (
        job_requests[f"num_{Outcome.CANCELLED_BY_DEPENDENCY}"]
        / job_requests["denominator"]
    )
    return job_requests.loc[:, "proportion"].to_frame()


def get_histogram(job_requests, column_name, axis_titles):
    title_x, title_y = axis_titles
    return (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(
            altair.X(column_name, bin=True).title(title_x),
            altair.Y("count()").title(title_y),
        )
    )


def get_scatter_plot(job_requests, column_names, axis_titles):
    encode_x, encode_y = column_names
    title_x, title_y = axis_titles
    return (
        altair.Chart(job_requests)
        .mark_circle()
        .encode(
            x=altair.X(encode_x).title(title_x),
            y=altair.Y(encode_y).title(title_y),
            tooltip=altair.Tooltip(list(job_requests.columns)),
        )
    )


def main():
    job_requests = get_job_requests(DATA_DIR / "job_requests" / "job_requests.csv")
    jobs = get_jobs(DATA_DIR / "jobs" / "jobs.csv")

    streamlit.header("Job requests")
    streamlit.subheader("Jobs that errored")

    proportion_histogram = get_histogram(
        calculate_proportions(jobs),
        "proportion",
        (
            "Number jobs that were cancelled by a dependency / Total number of jobs that errored",
            "Number of job requests",
        ),
    )
    streamlit.write(proportion_histogram)

    streamlit.subheader("Jobs and actions")
    col_1, col_2 = streamlit.columns(2)

    with col_1:
        num_jobs_histogram = get_histogram(
            job_requests, "num_jobs", ("Number of jobs", "Number of job requests")
        )
        streamlit.write(num_jobs_histogram)

    with col_2:
        num_actions_histogram = get_histogram(
            job_requests, "num_actions", ("Number of actions", "Number of job requests")
        )
        streamlit.write(num_actions_histogram)

    measure_histogram = get_histogram(
        job_requests,
        "measure",
        ("Number of jobs / Number of actions", "Number of job requests"),
    )
    streamlit.write(measure_histogram)

    scatter_plot = get_scatter_plot(
        job_requests,
        ("num_actions", "measure"),
        ("Number of actions", "Number of jobs / Number of actions"),
    )
    streamlit.write(scatter_plot)


if __name__ == "__main__":
    main()
