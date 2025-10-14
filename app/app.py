import os
import pathlib

import repositories


def main(repository):  # pragma: no cover
    # This is tested by tests.app.test_app.test_app, but coverage doesn't seem to
    # realise.
    repository.get_date_earliest_job_request_created()
    repository.get_date_latest_job_request_created()

    repository.get_job_requests(None, None)


if __name__ == "__main__":
    DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "data"))
    repository = repositories.Repository(DATA_DIR)
    main(repository)
