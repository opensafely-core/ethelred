import altair
import pandas
import pytest

from app import charts


def test_get_counts_bar_chart():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_counts_bar_chart(
        table, "column_1", ("Title for x", "Title for y")
    )
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["x"]["sort"] == "-y"
    assert chart_dict["encoding"]["y"]["aggregate"] == "count"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"


def test_get_histogram():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_histogram(table, "column_1", ("Title for x", "Title for y"))
    chart_dict = chart.to_dict()
    histogram_dict, strip_plot_dict = chart_dict["vconcat"]

    assert histogram_dict["encoding"]["x"]["field"] == "column_1"
    assert histogram_dict["encoding"]["x"]["title"] == "Title for x"
    assert histogram_dict["encoding"]["y"]["title"] == "Title for y"

    assert strip_plot_dict["encoding"]["x"]["field"] == "column_1"
    assert strip_plot_dict["encoding"]["x"]["title"] == "Title for x"


def test_get_scatter_plot():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_scatter_plot(
        table, ("column_1", "column_2"), ("Title for x", "Title for y")
    )
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["y"]["field"] == "column_2"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"


@pytest.mark.parametrize(
    "encodings,color_dict",
    [
        (
            dict(x="column_1", y="column_2", color="column_3:O"),
            {"field": "column_3", "type": "ordinal"},
        ),
        (
            dict(x="column_1", y="column_2"),
            {},
        ),
    ],
)
def test_grey_out_unselected(encodings, color_dict):
    table = pandas.DataFrame(
        {"column_1": range(10), "column_2": range(10), "column_3": range(10)}
    )
    chart = altair.Chart(table).mark_circle().encode(**encodings)
    selection = altair.selection_point(encodings=["x"], name="selection")
    chart = charts.grey_out_unselected(chart, selection)
    chart_dict = chart.to_dict()

    assert chart_dict["encoding"]["color"] == {
        "condition": {"param": "selection", **color_dict},
        "value": "lightgray",
    }


def test_highlight_focus_by_selection_in_context():
    table = pandas.DataFrame(
        {"column_1": range(10), "column_2": range(10), "column_3": range(10)}
    )
    chart = altair.Chart(table).mark_circle().encode(x="column_1", y="column_2")
    focus, context = charts.highlight_focus_by_selection_in_context(
        chart, chart, ["x", "y"]
    )
    focus_dict = focus.to_dict()
    context_dict = context.to_dict()
    (param,) = context_dict["params"]

    assert param["select"] == {"type": "point", "encodings": ["x", "y"]}

    expected = {"condition": {"param": param["name"]}, "value": "lightgray"}
    assert focus_dict["encoding"]["color"] == expected
    assert context_dict["encoding"]["color"] == expected
