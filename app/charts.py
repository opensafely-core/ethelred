import altair


def get_counts_bar_chart(job_requests, column_name, axis_titles):
    title_x, title_y = axis_titles
    return (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(
            altair.X(column_name).title(title_x).sort("-y"),
            altair.Y("count()").title(title_y),
        )
    )


def get_histogram(job_requests, column_name, axis_titles):
    title_x, title_y = axis_titles
    histogram = (
        altair.Chart(job_requests)
        .mark_bar()
        .encode(
            altair.X(column_name, bin=True).title(title_x),
            altair.Y("count()").title(title_y),
        )
    )
    strip_plot = (
        altair.Chart(job_requests)
        .mark_tick()
        .encode(
            altair.X(column_name).title(title_x),
        )
    )
    return histogram & strip_plot


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


def grey_out_unselected(chart, selection):
    color = chart.encoding.color
    color = color if color is not altair.Undefined else ""
    return chart.encode(
        color=altair.condition(selection, color, altair.value("lightgray"))
    )


def highlight_focus_by_selection_in_context(focus, context, selection_encodings):
    selection = altair.selection_point(encodings=selection_encodings)
    context = context.add_params(selection)

    focus = grey_out_unselected(focus, selection)
    context = grey_out_unselected(context, selection)
    return focus, context
