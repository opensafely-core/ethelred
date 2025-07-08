import pandas

from app import charts


def test_get_histogram():
    table = pandas.DataFrame({"column_1": range(10), "column_2": range(10)})
    chart = charts.get_histogram(table, "column_1", ("Title for x", "Title for y"))
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["x"]["field"] == "column_1"
    assert chart_dict["encoding"]["x"]["title"] == "Title for x"
    assert chart_dict["encoding"]["y"]["title"] == "Title for y"


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
