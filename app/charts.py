import altair


def get_bar_chart(data_frame, column_name, axis_titles, selection):
    title_x, title_y = axis_titles
    return (
        altair.Chart(data_frame)
        .mark_bar()
        .encode(
            altair.X(f"{column_name}:N").title(title_x).sort("-y"),
            altair.Y("count()").title(title_y),
            color=altair.condition(selection, "", altair.value("lightgray")),
        )
        .add_params(selection)
    )


def get_histogram(data_frame, column_name, axis_titles):
    title_x, title_y = axis_titles
    selection = altair.selection_interval(encodings=["x"])
    base = altair.Chart(data_frame)
    histogram = (
        base.mark_bar()
        .encode(
            altair.X(column_name, bin=True).title(""),
            altair.Y("count()").title(title_y),
            tooltip=[
                altair.Tooltip("count()").title(title_y),
                altair.Tooltip(column_name, bin=True).title("Bin"),
            ],
        )
        .transform_filter(selection)
    )
    strip_plot = (
        base.mark_tick()
        .encode(altair.X(column_name).title(title_x), tooltip=[])
        .add_params(selection)
        .properties(view=altair.ViewConfig(cursor="crosshair"))
    )
    return histogram & strip_plot


def get_scatter_plot(data_frame, column_names, axis_titles, selection):
    encode_x, encode_y = column_names
    title_x, title_y = axis_titles
    when_selected = altair.when(selection)
    return (
        altair.Chart(data_frame)
        .mark_circle()
        .encode(
            x=altair.X(encode_x).title(title_x),
            y=altair.Y(encode_y).title(title_y),
            color=altair.condition(selection, "", altair.value("lightgray")),
            tooltip=altair.Tooltip(list(data_frame.columns)),
            order=when_selected.then(altair.value(1)).otherwise(altair.value(0)),
        )
    )
