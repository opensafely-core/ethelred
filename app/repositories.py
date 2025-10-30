import abc

import duckdb
import pandas
from duckdb import sqltypes


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def get_earliest_login_event_date(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_latest_login_event_date(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_login_events_per_day(self, from_, to_):
        raise NotImplementedError

    @abc.abstractmethod
    def get_codelist_create_events_per_day(self, from_, to_):
        raise NotImplementedError


class Repository(AbstractRepository):
    def __init__(self, root_uri):
        self.login_events_uri = root_uri + "/opencodelists/login_events.csv"
        self.codelist_create_events_uri = (
            root_uri + "/opencodelists/codelist_create_events.csv"
        )

    def _call(self, uri, func, col):
        with duckdb.connect() as conn:
            rel = conn.read_csv(uri)
            val, *_ = getattr(rel, func)(col).fetchone()
        return val

    def get_earliest_login_event_date(self):
        return self._call(self.login_events_uri, "min", "login_at").date()

    def get_latest_login_event_date(self):
        return self._call(self.login_events_uri, "max", "login_at").date()

    def get_login_events_per_day(self, from_, to_):  # pragma: no cover
        return _get_events_per_day(self.login_events_uri, "login_at", from_, to_)

    def get_codelist_create_events_per_day(self, from_, to_):  # pragma: no cover
        return _get_events_per_day(
            self.codelist_create_events_uri, "created_at", from_, to_
        )


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
