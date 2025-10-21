import abc

import duckdb
import pandas


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def get_earliest_login_date(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_latest_login_date(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_logins_per_day(self, from_, to_):
        raise NotImplementedError


class Repository(AbstractRepository):
    def __init__(self, root_uri):
        self.opencodelists_logins_uri = (
            root_uri + "/opencodelists_logins/opencodelists_logins.csv"
        )

    def _call(self, uri, func, col):
        with duckdb.connect() as conn:
            rel = conn.read_csv(uri)
            val, *_ = getattr(rel, func)(col).fetchone()
        return val

    def get_earliest_login_date(self):
        return self._call(self.opencodelists_logins_uri, "min", "login_at").date()

    def get_latest_login_date(self):
        return self._call(self.opencodelists_logins_uri, "max", "login_at").date()

    def get_logins_per_day(self, from_, to_):
        assert from_ <= to_
        with duckdb.connect() as conn:
            logins_per_day_relation = conn.sql(
                """
                SELECT
                    login_on AS date,
                    COUNT(*) AS count
                FROM (
                    SELECT
                        CAST(login_at AS DATE) AS login_on
                    FROM read_csv($uri)
                    WHERE login_at >= $from AND login_at <= $to
                )
                GROUP BY login_on
                ORDER BY login_on
                """,
                params={
                    "uri": self.opencodelists_logins_uri,
                    "from": from_,
                    "to": to_,
                },
            )
            logins_per_day = logins_per_day_relation.to_df()

        # interpolate counts of zero for days without logins
        idx = pandas.date_range(from_, to_, freq="D", normalize=True, name="date")
        return logins_per_day.set_index("date").reindex(idx).fillna(0).reset_index()
