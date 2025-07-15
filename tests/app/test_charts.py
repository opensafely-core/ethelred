import altair
import pandas

from app import charts


def test_get_bar_chart():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    selection = altair.selection_point(name="my_selection")
    chart = charts.get_bar_chart(
        table, "column_1", ("Title for x", "Title for y"), selection
    )
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["x"]["sort"] == "-y"
    assert chart_dict["encoding"]["y"]["aggregate"] == "count"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"
    assert chart_dict["encoding"]["color"] == {
        "condition": {"param": "my_selection"},
        "value": "lightgray",
    }
    assert chart_dict["params"][0]["name"] == "my_selection"


def test_get_histogram():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_histogram(table, "column_1", ("Title for x", "Title for y"))
    chart_dict = chart.to_dict()
    (param,) = chart_dict["params"]
    histogram_dict, strip_plot_dict = chart_dict["vconcat"]

    assert param["select"] == {"type": "interval", "encodings": ["x"]}

    assert histogram_dict["encoding"]["x"]["field"] == "column_1"
    assert histogram_dict["encoding"]["x"]["title"] == ""
    assert histogram_dict["encoding"]["y"]["title"] == "Title for y"
    assert histogram_dict["transform"] == [{"filter": {"param": param["name"]}}]

    assert strip_plot_dict["encoding"]["x"]["field"] == "column_1"
    assert strip_plot_dict["encoding"]["x"]["title"] == "Title for x"


def test_get_scatter_plot():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    selection = altair.selection_point(name="my_selection")
    chart = charts.get_scatter_plot(
        table, ("column_1", "column_2"), ("Title for x", "Title for y"), selection
    )
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["y"]["field"] == "column_2"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"
    assert chart_dict["encoding"]["color"] == {
        "condition": {"param": "my_selection"},
        "value": "lightgray",
    }
