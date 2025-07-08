import altair


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
