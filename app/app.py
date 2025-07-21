import os
import pathlib

import repositories


def main(repository):  # pragma: no cover
    # This is tested by tests.app.test_app.test_app, but coverage doesn't seem to
    # realise.
    import altair
    import streamlit

    import charts

    date_earliest = repository.get_date_earliest_job_request_created()
    date_latest = repository.get_date_latest_job_request_created()

    with streamlit.sidebar:
        from_ = streamlit.date_input(
            "From",
            value=date_earliest,
            min_value=date_earliest,
            max_value=date_latest,
            help=(
                "Include job requests and their associated jobs "
                + "that were created on or after this date"
            ),
        )
        to_ = streamlit.date_input(
            "To",
            value=date_latest,
            min_value=date_earliest,
            max_value=date_latest,
            help=(
                "Include job requests and their associated jobs "
                + "that were created on or before this date"
            ),
        )
        if not from_ < to_:
            streamlit.error("The *From* date must come before the *To* date.")
            from_ = date_earliest
            to_ = date_latest

    job_requests = repository.get_job_requests(from_, to_)

    streamlit.header("Job requests")
    streamlit.subheader("Jobs that failed")

    prop_dependency_failed_jobs_histogram = charts.get_histogram(
        job_requests,
        "prop:Q",
        (
            "Number of jobs where a dependency failed / Number of jobs that failed",
            "Number of job requests",
        ),
    ).transform_calculate(
        prop=altair.datum.num_dependency_failed_jobs / altair.datum.num_failed_jobs
    )
    streamlit.write(prop_dependency_failed_jobs_histogram)

    streamlit.subheader("Jobs and actions")
    col_1, col_2 = streamlit.columns(2)

    with col_1:
        num_jobs_histogram = charts.get_histogram(
            job_requests, "num_jobs", ("Number of jobs", "Number of job requests")
        )
        streamlit.write(num_jobs_histogram)

    with col_2:
        num_actions_histogram = charts.get_histogram(
            job_requests, "num_actions", ("Number of actions", "Number of job requests")
        )
        streamlit.write(num_actions_histogram)

    prop_jobs_histogram = charts.get_histogram(
        job_requests,
        "prop:Q",
        ("Number of jobs / Number of actions", "Number of job requests"),
    ).transform_calculate(prop=altair.datum.num_jobs / altair.datum.num_actions)
    streamlit.write(prop_jobs_histogram)

    username_selection = altair.selection_point(fields=["username"])
    scatter_plot = charts.get_scatter_plot(
        job_requests,
        ("num_actions", "prop:Q"),
        ("Number of actions", "Number of jobs / Number of actions"),
        username_selection,
    ).transform_calculate(prop=altair.datum.num_jobs / altair.datum.num_actions)
    username_bar_chart = charts.get_bar_chart(
        job_requests,
        "username",
        ("Username", "Number of job requests"),
        username_selection,
    )
    streamlit.write(scatter_plot & username_bar_chart)


if __name__ == "__main__":
    DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "data"))
    repository = repositories.Repository(DATA_DIR)
    main(repository)
