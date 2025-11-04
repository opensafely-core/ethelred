import os
import pathlib

import repositories


def main(repository):  # pragma: no cover
    # This is tested by tests.app.test_app.test_app, but coverage doesn't seem to
    # realise.
    import altair
    import streamlit

    with streamlit.sidebar:
        earliest_event_date = repository.get_earliest_login_event_date()
        latest_event_date = repository.get_latest_login_event_date()

        initial_from = latest_event_date.replace(month=1, day=1)
        from_ = streamlit.date_input(
            "From",
            value=initial_from,
            min_value=earliest_event_date,
            max_value=latest_event_date,
            help="The earliest date to include",
        )

        initial_to = latest_event_date
        to_ = streamlit.date_input(
            "To",
            value=initial_to,
            min_value=earliest_event_date,
            max_value=latest_event_date,
            help="The latest date to include",
        )

        if not from_ < to_:
            streamlit.error("The *From* date must come before the *To* date.")
            from_ = initial_from
            to_ = initial_to

    streamlit.title("Ethelred")

    streamlit.header("OpenCodelists")

    lhs_column, rhs_column = streamlit.columns(2)

    with lhs_column:
        streamlit.metric(
            "Number of users logged in",
            "{:,}".format(repository.get_num_users_logged_in(from_, to_)),
            border=True,
            help="The number of users logged in "
            + f"from {from_:%Y/%m/%d} to {to_:%Y/%m/%d}",
        )

    with rhs_column:
        streamlit.metric(
            "Number of codelists created",
            "{:,}".format(repository.get_num_codelists_created(from_, to_)),
            border=True,
            help="The number of codelists created "
            + f"from {from_:%Y/%m/%d} to {to_:%Y/%m/%d}",
        )

    streamlit.markdown(
        f"Number of login events per day from {from_:%Y/%m/%d} to {to_:%Y/%m/%d} in blue, "
        + "compared to the 28 day rolling mean in red"
    )

    def timeseries(events_per_day):
        base_chart = altair.Chart(events_per_day)
        count_chart = base_chart.mark_line().encode(x="date", y="count")
        rolling_mean_chart = (
            base_chart.mark_line(color="red")
            .transform_window(rolling_mean="mean(count)", frame=[-27, 0])
            .encode(x="date", y="rolling_mean:Q")
        )
        layer_chart = (
            (count_chart + rolling_mean_chart)
            .configure_axis(title=None)
            .configure_line(interpolate="monotone")
        )
        return layer_chart

    streamlit.write(timeseries(repository.get_login_events_per_day(from_, to_)))

    with streamlit.expander("About login events"):
        streamlit.markdown(
            f"""
            Currently, each of the
            {repository.get_num_users_logged_in(from_, to_):,}
            users is associated with a single login event:
            the latest (most recent) login event,
            at the time the data were extracted on {to_:%Y/%m/%d}.
            For a given user, the time of the latest login event will change
            from one extract to another,
            if they login after the first extract and before the second extract.
            """
        )

    streamlit.markdown(
        f"Number of codelist create events per day from {from_:%Y/%m/%d} to {to_:%Y/%m/%d} in blue, "
        + "compared to the 28 day rolling mean in red"
    )

    streamlit.write(
        timeseries(repository.get_codelist_create_events_per_day(from_, to_))
    )


if __name__ == "__main__":
    root_uri = os.environ.get(
        "REPOSITORY_ROOT_URI", pathlib.Path("data").resolve().as_uri()
    )
    repository = repositories.Repository(root_uri)
    main(repository)
