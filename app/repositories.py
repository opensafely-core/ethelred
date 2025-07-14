import pandas


class Repository:
    def __init__(self, root_dir):
        self.job_requests_csv = root_dir / "job_requests" / "job_requests.csv"

    def get_job_requests(self):
        job_requests = pandas.read_csv(self.job_requests_csv)
        job_requests["measure"] = job_requests["num_jobs"] / job_requests["num_actions"]
        return job_requests
