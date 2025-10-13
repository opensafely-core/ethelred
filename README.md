# Ethelred

[Ethelred][1] is an Old English personal name, meaning "noble counsel" or "well-advised".
This Ethelred hopes to avoid the fate of [its namesake][2],
who was infamously not ready.

This Ethelred is:

* several tasks for extracting, transforming, and loading data from multiple, heterogeneous sources.
  You will find them in `tasks`.
* a [Streamlit][] app for representing that data to facilitate more effective decision-making.
  You will find it in `app`.

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

## Docs

Glad you asked!
See the [README](docs/README.md) in the `docs` directory.

[1]: https://en.wikipedia.org/wiki/%C3%86thelred
[2]: https://en.wikipedia.org/wiki/%C3%86thelred_the_Unready
[3]: https://github.com/opensafely-core/job-server/blob/main/DEVELOPERS.md
[4]: https://github.com/settings/personal-access-tokens
[5]: https://github.com/opensafely-core/opencodelists/blob/main/DEVELOPERS.md
[Streamlit]: https://streamlit.io/
