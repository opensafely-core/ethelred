import abc

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
    def __init__(self, database_url):
        self._logins = pandas.read_sql_table("opencodelists_logins", database_url)

    def get_earliest_login_date(self):
        return self._logins["login_at"].min().to_pydatetime()

    def get_latest_login_date(self):
        return self._logins["login_at"].max().to_pydatetime()

    def get_logins_per_day(self, from_, to_):
        assert from_ <= to_
        # Indexing into a DatetimeIndex with a string when a datetime.date is available
        # feels wrong, but the alternatives are cumbersome.
        from_, to_ = [x.isoformat() for x in (from_, to_)]
        logins = self._logins.set_index("login_at").sort_index().loc[from_:to_]
        logins_per_day = (
            logins.resample("D")
            .count()
            .reset_index()
            .rename(columns={"login_at": "date", "email_hash": "count"})
        )
        return logins_per_day
