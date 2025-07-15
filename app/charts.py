import altair


def get_counts_bar_chart(job_requests, column_name, axis_titles, selection):
    title_x, title_y = axis_titles
    return (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(
            altair.X(column_name).title(title_x).sort("-y"),
            altair.Y("count()").title(title_y),
            color=altair.condition(selection, "", altair.value("lightgray")),
        )
        .add_params(selection)
    )


def get_histogram(job_requests, column_name, axis_titles):
    title_x, title_y = axis_titles
    selection = altair.selection_interval(encodings=["x"])
    histogram = (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(
            altair.X(column_name, bin=True).title(""),
            altair.Y("count()").title(title_y),
        )
        .transform_filter(selection)
    )
    strip_plot = (
        altair.Chart(job_requests)
        .mark_tick()
        .encode(
            altair.X(column_name).title(title_x),
        )
        .add_params(selection)
    )
    return histogram & strip_plot


def get_scatter_plot(job_requests, column_names, axis_titles, selection):
    encode_x, encode_y = column_names
    title_x, title_y = axis_titles
    return (
        altair.Chart(job_requests)
        .mark_circle()
        .encode(
            x=altair.X(encode_x).title(title_x),
            y=altair.Y(encode_y).title(title_y),
            color=altair.condition(selection, "", altair.value("lightgray")),
            tooltip=altair.Tooltip(list(job_requests.columns)),
        )
    )
