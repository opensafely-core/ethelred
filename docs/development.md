# Development

## Setup

Different tasks have different data dependencies.
These are:

* a Job Server PostgreSQL database.
  Refer to [Job Server's][3] developer documentation for setup instructions.
* an OpenCodelists SQLite database.
  Refer to [OpenCodelists's][5] developer documentation for setup instructions.
* a series of GitHub fine-grained [Personal Access Tokens][4] (PATs):
  * opensafely organisation: "Actions (read-only)" and "Pull Requests (read-only)" permissions,
  * opensafely-core organisation: "Pull Requests (read-only)" permission,
  * ebmdatalab organisation: "Pull Requests (read-only)" permission,
  * bennettoxford organisation: "Pull Requests (read-only)" permission.

(Note that the opensafely-core, ebmdatalab and bennettoxford PATs are only needed for running the `get_prs` task
and can be left empty if you aren't going to run it.)

When you've got the data dependencies you need,
copy `dotenv` to `.env` and, if necessary, update `.env`.

Next, run the following commands:

```sh
just devenv
source .venv/bin/activate
just tasks-list # lists all tasks
just tasks-run <task> # runs individual tasks
just run app/app.py
```

[3]: https://github.com/opensafely-core/job-server/blob/main/DEVELOPERS.md
[4]: https://github.com/settings/personal-access-tokens
[5]: https://github.com/opensafely-core/opencodelists/blob/main/DEVELOPERS.md
