import duckdb
import pandas
from duckdb import sqltypes


class Repository:
    def __init__(self, root_uri):
        self.uris = {
            "login_events": root_uri + "/opencodelists/login_events.csv",
            "codelist_create_events": root_uri
            + "/opencodelists/codelist_create_events.csv",
        }

    def get_earliest_login_event_date(self):  # pragma: no cover
        return _get_scalar_result(self.uris["login_events"], "min", "login_at").date()

    def get_latest_login_event_date(self):  # pragma: no cover
        return _get_scalar_result(self.uris["login_events"], "max", "login_at").date()

    def get_login_events_per_day(self, from_, to_):  # pragma: no cover
        return _get_events_per_day(self.uris["login_events"], "login_at", from_, to_)

    def get_codelist_create_events_per_day(self, from_, to_):  # pragma: no cover
        return _get_events_per_day(
            self.uris["codelist_create_events"], "created_at", from_, to_
        )


def _get_scalar_result(uri, func, col):
    with duckdb.connect() as conn:
        rel = conn.read_csv(uri)
        val, *_ = getattr(rel, func)(col).fetchone()
    return val


def _get_events_per_day(uri, col, from_, to_):
    assert from_ <= to_
    with duckdb.connect() as conn:
        rel = conn.read_csv(uri)
        event_at = duckdb.ColumnExpression(col)
        rel = rel.filter(event_at >= from_)
        rel = rel.filter(event_at <= to_)
        rel = rel.select(event_at.cast(sqltypes.DATE).alias("event_on"))
        rel = rel.order("event_on")
        rel = rel.aggregate(
            [
                duckdb.ColumnExpression("event_on").alias("date"),
                duckdb.FunctionExpression("count").alias("count"),
            ],
            "event_on",
        )

        events_per_day = rel.to_df()

    # interpolate counts of zero for days without events
    idx = pandas.date_range(from_, to_, freq="D", normalize=True, name="date")
    return events_per_day.set_index("date").reindex(idx).fillna(0).reset_index()
