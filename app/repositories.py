import abc

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
        self.job_requests_csv = root_dir / "job_requests" / "job_requests.csv"
        self.jobs_csv = root_dir / "jobs" / "jobs.csv"

    def get_job_requests(self):
        job_requests = pandas.read_csv(self.job_requests_csv)
        return job_requests

    def get_jobs(self):
        jobs = pandas.read_csv(self.jobs_csv)
        return jobs

    @staticmethod
    def calculate_proportions(jobs):
        """
        Returns a one row per job request DataFrame with a single column "proportion"
        that contains the proportion of jobs cancelled by dependency out of all
        jobs that either errored or were cancelled by dependency.

        Job requests with no jobs that errored or were cancelled by dependency
        are filtered out.
        """
        job_requests = (
            jobs.groupby(["job_request_id", "outcome"])
            .size()
            .unstack(fill_value=0)
            .add_prefix("num_")
        )
        job_requests["denominator"] = (
            job_requests["num_errored"] + job_requests["num_cancelled by dependency"]
        )
        job_requests = job_requests.loc[job_requests["denominator"] > 0]
        job_requests["proportion"] = (
            job_requests["num_cancelled by dependency"] / job_requests["denominator"]
        )
        return job_requests.loc[:, "proportion"].to_frame()
