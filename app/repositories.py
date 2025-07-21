import abc
import pathlib

import pandas


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def get_job_requests(self):
        # It's not possible to inherit from this class without overriding this method,
        # but coverage doesn't seem to realise.
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_jobs(self):
        # It's not possible to inherit from this class without overriding this method,
        # but coverage doesn't seem to realise.
        raise NotImplementedError  # pragma: no cover


class Repository(AbstractRepository):
    def __init__(self, root_dir):
        root_dir = pathlib.Path(root_dir)
        self.job_requests_csv = root_dir / "job_requests" / "job_requests.csv"
        self.jobs_csv = root_dir / "jobs" / "jobs.csv"

    @property
    def _job_requests(self):
        return pandas.read_csv(self.job_requests_csv, parse_dates=["created_at"])

    def get_date_earliest_job_request_created(self):
        return self._job_requests["created_at"].min().to_pydatetime().date()

    def get_date_latest_job_request_created(self):
        return self._job_requests["created_at"].max().to_pydatetime().date()

    def get_job_requests(self):
        return self._job_requests

    def get_jobs(self):
        return pandas.read_csv(self.jobs_csv)
