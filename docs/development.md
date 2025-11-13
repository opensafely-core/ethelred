# Development

## System requirements

### just

Follow installation instructions from the [Just Programmer's Manual](https://just.systems/man/en/chapter_4.html) for your OS.

### uv

Follow installation instructions from the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/) for your OS.

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
just run python -m tasks list # lists all tasks
just run python -m tasks run <task> # runs individual tasks
just run streamlit run app/app.py
```

## Dependency management
Dependencies are managed with `uv`.

### Overview
See the [uv documentation](https://docs.astral.sh/uv/concepts/projects/dependencies) for details on usage.
Commands for adding, removing or modifying constraints of dependencies will automatically respect the
global timestamp cutoff specified in the `pyproject.toml`:
```toml
[tool.uv]
exclude-newer = "YYYY-MM-DDTHH:MM:SSZ"
```
Changes to dependencies should be made via `uv` commands, or by modifying `pyproject.toml` directly followed by
[locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) via `uv` or `just` commands like
`just devenv` or `just upgrade-all`. You should not modify `uv.lock` manually.

Note that `uv.lock` must be reproducible from `pyproject.toml`. Otherwise, `just check` will fail.
If `just check` errors saying that the timestamps must match, you might have modified one file but not the other:
  - If you modified `pyproject.toml`, you must update `uv.lock` via `uv lock` / `just upgrade-all` or similar.
  - If you did not modify `pyproject.toml` but have changes in `uv.lock`, you should revert the changes to `uv.lock`,
  modify `pyproject.toml` as you require, then run `uv lock` to update `uv.lock`.

The timestamp cutoff should usually be set to midnight UTC of a past date.
In general, the date is expected to be between 7 and 14 days ago as a result of automated weekly dependency updates.

If you require a package version that is newer than the cutoff allows, you can manually bump the global cutoff
date as described below.

### Manually bumping the cutoff date
The cutoff timestamp can be modified to a more recent date either manually in the `pyproject.toml`
or with `just bump-uv-cutoff <days-ago>`.
For example, to set the cutoff to today's date and upgrade all dependencies, run:
```
just bump-uv-cutoff 0
just upgrade-all
```

[5]: https://github.com/opensafely-core/opencodelists/blob/main/DEVELOPERS.md
