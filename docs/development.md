# Development

## Setup

Different tasks have different data dependencies.
These are:

* an OpenCodelists SQLite database.
  Refer to [OpenCodelists's][5] developer documentation for setup instructions.

When you've got the data dependencies you need,
copy `dotenv` to `.env` and, if necessary, update `.env`.

Next, run the following commands:

```sh
just devenv
source .venv/bin/activate
source .env
python -m tasks list # lists all tasks
python -m tasks run <task> # runs individual tasks
just run app/app.py
```

[5]: https://github.com/opensafely-core/opencodelists/blob/main/DEVELOPERS.md
