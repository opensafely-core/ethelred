import os
import pathlib

import duckdb
import pandas
from duckdb import sqltypes


def main(repository):  # pragma: no cover  # called in subprocess in tests
    import altair
    import streamlit

    streamlit.title("Ethelred: Delivery Metrics")

    streamlit.header("PRs created per day")

    def timeseries(events_per_day):
        base_chart = altair.Chart(events_per_day)
        count_chart = base_chart.mark_line().encode(x="date", y="count")
        rolling_mean_chart = (
            base_chart.mark_line(color="red")
            .transform_window(rolling_mean="mean(count)", frame=[-27, 0])
            .encode(x="date", y="rolling_mean:Q")
        )
        layer_chart = (count_chart + rolling_mean_chart).configure_axis(title=None)
        return layer_chart

    streamlit.write(timeseries(repository.get_prs_created_per_day()))


class Repository:
    def __init__(self, uri):
        self._uri = uri

    def get_prs_created_per_day(self):
        with duckdb.connect() as conn:
            rel = conn.read_csv(self._uri)
            created_at = duckdb.ColumnExpression("created_at")
            created_on = created_at.cast(sqltypes.DATE).alias("created_on")
            rel = rel.select(created_on)
            rel = rel.order("created_on")
            rel = rel.aggregate(
                [
                    duckdb.ColumnExpression("created_on").alias("date"),
                    duckdb.FunctionExpression("count").alias("count"),
                ],  # type: ignore
                "created_on",
            )
            created_per_day = rel.to_df()

        # interpolate counts of zero for days without events
        idx = pandas.date_range(
            created_per_day["date"].min(),
            created_per_day["date"].max(),
            freq="D",
            name="date",
        )
        return (
            created_per_day.set_index("date").reindex(idx, fill_value=0).reset_index()
        )


if __name__ == "__main__":
    root_uri = os.environ.get(
        "REPOSITORY_ROOT_URI", pathlib.Path("data").resolve().as_uri()
    )
    repository = Repository(root_uri + "/github/opensafely-core/prs.csv")
    main(repository)
