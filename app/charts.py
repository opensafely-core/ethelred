"""
Functions that return charts of different types.

Avoid passing the type of measurement for the encoded field:
quantitative (Q), temporal (T), ordinal (O), or nominal (N). Altair is able
to determine this from the data frame. If Altair isn't, then the encoded field doesn't
exist in the data frame.

If the type of measurement is passed when the encoded field doesn't exist in the data
frame, then the end-to-end test will pass when it should fail.

As an example, given the following chart:

>>> chart = altair.Chart(pandas.DataFrame({"column_1": range(10)})).mark_bar()

Avoid doing this:

>>> chart = chart.encode(altair.X("column_1:Q"))

Instead, do this:

>>> chart = chart.encode(altair.X("column_1"))
"""

import altair
import pandas  # noqa: F401


def get_bar_chart(data_frame, column_name, axis_titles, selection):
    title_x, title_y = axis_titles
    return (
        altair.Chart(data_frame)
        .mark_bar()
        .encode(
            x=altair.X(column_name).title(title_x).sort("-y"),
            y=altair.Y("count()").title(title_y),
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
            x=altair.X(column_name, bin=True).title(""),
            y=altair.Y("count()").title(title_y),
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
