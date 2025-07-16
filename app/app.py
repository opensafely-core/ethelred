import os
import pathlib

import repositories


def main(repository):  # pragma: no cover
    # This is tested by tests.app.test_app.test_app, but coverage doesn't seem to
    # realise.
    import altair
    import pandas
    import streamlit

    import charts

    job_requests = repository.get_job_requests()
    jobs = repository.get_jobs()

    streamlit.header("Job requests")

    streamlit.subheader("Creation date range (inclusive)")
    streamlit.date_input(
        "Start date", key="start_date", value=job_requests["created_at"].min()
    )
    streamlit.date_input(
        "End date", key="end_date", value=job_requests["created_at"].max()
    )
    job_requests_in_date_range = job_requests.loc[
        job_requests["created_at"].between(
            pandas.to_datetime(streamlit.session_state.start_date, utc=True),
            pandas.to_datetime(streamlit.session_state.end_date, utc=True)
            + pandas.Timedelta(days=1),
        )
    ]
    jobs_in_date_range = jobs.loc[
        jobs["job_request_id"].isin(job_requests_in_date_range["id"])
    ]

    streamlit.subheader("Jobs that errored")

    proportion_histogram = charts.get_histogram(
        repository.calculate_proportions(jobs_in_date_range),
        "proportion",
        (
            "Number of jobs that were cancelled by a dependency / Total number of jobs that errored",
            "Number of job requests",
        ),
    )
    streamlit.write(proportion_histogram)

    streamlit.subheader("Jobs and actions")
    col_1, col_2 = streamlit.columns(2)

    with col_1:
        num_jobs_histogram = charts.get_histogram(
            job_requests_in_date_range,
            "num_jobs",
            ("Number of jobs", "Number of job requests"),
        )
        streamlit.write(num_jobs_histogram)

    with col_2:
        num_actions_histogram = charts.get_histogram(
            job_requests_in_date_range,
            "num_actions",
            ("Number of actions", "Number of job requests"),
        )
        streamlit.write(num_actions_histogram)

    num_jobs_over_num_actions_histogram = charts.get_histogram(
        job_requests_in_date_range,
        "num_jobs_over_num_actions",
        ("Number of jobs / Number of actions", "Number of job requests"),
    )
    streamlit.write(num_jobs_over_num_actions_histogram)

    username_selection = altair.selection_point(fields=["username"])
    scatter_plot = charts.get_scatter_plot(
        job_requests_in_date_range,
        ("num_actions", "num_jobs_over_num_actions"),
        ("Number of actions", "Number of jobs / Number of actions"),
        username_selection,
    )
    username_bar_chart = charts.get_bar_chart(
        job_requests_in_date_range,
        "username",
        ("Username", "Number of job requests"),
        username_selection,
    )
    streamlit.write(scatter_plot & username_bar_chart)


if __name__ == "__main__":
    DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "data"))
    repository = repositories.Repository(DATA_DIR)
    main(repository)
