import pathlib

import pandas


class Repository:
    def __init__(self, root_dir):
        root_dir = pathlib.Path(root_dir)
        self.job_requests_csv = root_dir / "job_requests" / "job_requests.csv"
        self.jobs_csv = root_dir / "jobs" / "jobs.csv"

    @property
    def _job_requests(self):
        return pandas.read_csv(self.job_requests_csv, parse_dates=["created_at"])

    def get_earliest_job_request_created_at(self):
        return self._job_requests["created_at"].min().to_pydatetime()

    def get_latest_job_request_created_at(self):
        return self._job_requests["created_at"].max().to_pydatetime()

    def get_job_requests(self):
        return self._job_requests

    def get_jobs(self):
        return pandas.read_csv(self.jobs_csv)
