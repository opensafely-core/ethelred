import altair
import pandas

from app import charts


def test_get_bar_chart():
    data_frame = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    selection = altair.selection_point(name="my_selection")
    chart = charts.get_bar_chart(
        data_frame, "column_1", ("Title for x", "Title for y"), selection
    )
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"
    assert chart_dict["encoding"]["color"] == {
        "condition": {"param": "my_selection"},
        "value": "lightgray",
    }
    assert chart_dict["params"][0]["name"] == "my_selection"


def test_get_histogram():
    data_frame = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_histogram(data_frame, "column_1", ("Title for x", "Title for y"))
    histogram_dict, strip_plot_dict = chart.to_dict().get("vconcat")
    assert histogram_dict["encoding"]["x"]["field"] == "column_1"
    assert histogram_dict["encoding"]["x"]["title"] == ""
    assert histogram_dict["encoding"]["y"]["title"] == "Title for y"
    assert strip_plot_dict["encoding"]["x"]["field"] == "column_1"
    assert strip_plot_dict["encoding"]["x"]["title"] == "Title for x"
    assert strip_plot_dict["encoding"]["tooltip"] == []  # no tooltip


def test_get_scatter_plot():
    data_frame = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    selection = altair.selection_point(name="my_selection")
    chart = charts.get_scatter_plot(
        data_frame, ("column_1", "column_2"), ("Title for x", "Title for y"), selection
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
