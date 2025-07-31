# Ethelred

[Ethelred][1] is an Old English personal name, meaning "noble counsel" or "well-advised".
This Ethelred hopes to avoid the fate of [its namesake][2],
who was infamously not ready.

This Ethelred is:

* several tasks for extracting, transforming, and loading data.
  You will find them in `tasks`.
* a [Streamlit][] app for representing data.
  You will find it in `app`.

## Setup

Ethelred needs a Job Server database.
[Job Server's developer documentation][3] tells you how to get one.
When you've got one,
copy `dotenv` to `.env` and, if necessary, update `.env`.

You will also need a fine-grained [personal access token][4] with "Actions (read-only)" permissions
and the resource owner set to the "opensafely" organisation.
When you have one, add it to `.env` with `GITHUB_WORKFLOW_RUNS_TOKEN` as the key.

Next, run the following commands:

```sh
just devenv
source .venv/bin/activate
python -m tasks.get_project_definitions
python -m tasks.get_job_requests
python -m tasks.get_jobs
python -m tasks.get_workflow_runs
just run app/app.py
```

## Docs

Glad you asked!
See the [README](docs/README.md) in the `docs` directory.

[1]: https://en.wikipedia.org/wiki/%C3%86thelred
[2]: https://en.wikipedia.org/wiki/%C3%86thelred_the_Unready
[3]: https://github.com/opensafely-core/job-server/blob/main/DEVELOPERS.md
[4]: https://github.com/settings/personal-access-tokens
[Streamlit]: https://streamlit.io/
