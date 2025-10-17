import os

import repositories


def _main(repository):  # pragma: no cover
    # This is tested by tests.app.test_app.test_app, but coverage doesn't seem to
    # realise.
    import altair
    import streamlit

    with streamlit.sidebar:
        earliest_login_date = repository.get_earliest_login_date()
        latest_login_date = repository.get_latest_login_date()

        initial_from = latest_login_date.replace(month=1, day=1)
        from_ = streamlit.date_input(
            "From",
            value=initial_from,
            min_value=earliest_login_date,
            max_value=latest_login_date,
            help="The earliest date to include",
        )

        initial_to = latest_login_date
        to_ = streamlit.date_input(
            "To",
            value=initial_to,
            min_value=earliest_login_date,
            max_value=latest_login_date,
            help="The latest date to include",
        )

        if not from_ < to_:
            streamlit.error("The *From* date must come before the *To* date.")
            from_ = initial_from
            to_ = initial_to

    streamlit.title("Ethelred")
    streamlit.button("Log out", on_click=streamlit.logout)

    streamlit.header("OpenCodelists")

    streamlit.markdown(
        f"Number of logins per day from {from_:%Y/%m/%d} to {to_:%Y/%m/%d} in blue, "
        + "compared to the 28 day rolling mean in red"
    )

    base_chart = altair.Chart(repository.get_logins_per_day(from_, to_))
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
    streamlit.write(layer_chart)


if __name__ == "__main__":
    import streamlit

    streamlit._secrets_singleton._secrets = {
        "auth": {
            "redirect_uri": os.environ["AUTH_REDIRECT_URI"],
            "cookie_secret": os.environ["AUTH_COOKIE_SECRET"],
            "client_id": os.environ["AUTH_CLIENT_ID"],
            "client_secret": os.environ["AUTH_CLIENT_SECRET"],
            "server_metadata_url": os.environ["AUTH_SERVER_METADATA_URL"],
        }
    }

    # user.is_logged_in is accessible only after loading secrets
    if streamlit.user.is_logged_in:
        database_url = os.environ.get("ETHELRED_DATABASE_URL")
        repository = repositories.Repository(database_url)
        _main(repository)
    else:
        streamlit.login()
