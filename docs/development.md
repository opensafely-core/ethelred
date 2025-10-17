# Development

## Setup

Ethelred needs a Job Server PostgreSQL database and an OpenCodelists SQLite database.
Refer to [Job Server's][3] and [OpenCodelists's][5] developer documentation for how to set these up.

Ethelred needs a fine-grained [Personal Access Token][4] (PAT) with the "Actions (read-only)" permission.
The PAT should access resources owned by the opensafely organisation.

When you've got the databases and a PAT,
copy `dotenv` to `.env` and, if necessary, update `.env`.

Next, run the following commands:

```sh
just devenv
source .venv/bin/activate
python -m tasks list # lists all tasks
python -m tasks run <task> # runs individual tasks
just run app/app.py
```

[3]: https://github.com/opensafely-core/job-server/blob/main/DEVELOPERS.md
[4]: https://github.com/settings/personal-access-tokens
[5]: https://github.com/opensafely-core/opencodelists/blob/main/DEVELOPERS.md
