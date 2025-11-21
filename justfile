set dotenv-load := true

# List available recipes and their arguments
default:
    @{{ just_executable() }} --list

# Check if a .env exists
_checkenv:
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ ! -f .env ]]; then
        echo "No '.env' file found; please create one from dotenv"
        exit 1
    fi

# Remove the virtual environment
clean:
    rm -rf .venv

# Upgrade a single package to the latest version as of the cutoff in pyproject.toml
upgrade-package package: && devenv
    uv lock --upgrade-package {{ package }}

# Upgrade all packages to the latest versions as of the cutoff in pyproject.toml
upgrade-all: && devenv
    uv lock --upgrade

# Bump the cutoff in pyproject.toml to `days` days ago at midnight UTC
bump-uv-cutoff days="7":
    #!/usr/bin/env -S uvx --with tomlkit python3.13

    import datetime
    import tomlkit

    with open("pyproject.toml", "rb") as f:
        content = tomlkit.load(f)

    new_datetime = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=int("{{ days }}"))
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    new_timestamp = new_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    if existing_timestamp := content["tool"]["uv"].get("exclude-newer"):
        if new_datetime < datetime.datetime.fromisoformat(existing_timestamp):
            print(
                f"Existing cutoff {existing_timestamp} is more recent than {new_timestamp}, not updating."
            )
            exit(0)
    content["tool"]["uv"]["exclude-newer"] = new_timestamp

    with open("pyproject.toml", "w") as f:
        tomlkit.dump(content, f)

# Upgrade all packages to the latest versions (used by the update-dependencies GitHub Actions workflow)
update-dependencies: bump-uv-cutoff upgrade-all

# Install pre-commit hook
install-pre-commit:
    test -f .git/hooks/pre-commit || uv run pre-commit install

# Install prod requirements into the virtual environment and remove all other packages
prodenv:
    uv sync --no-dev

# Install dev requirements into the virtual environment
devenv: && install-pre-commit
    uv sync --inexact

# Run a command in the virtual environment
run *args: _checkenv
    #!/usr/bin/env bash
    set -euo pipefail

    # The --no-dev flag ensures that uv doesn't install dev dependencies before it runs
    # the command. However, uv doesn't remove dev dependencies, if they are present.
    # To run the command with prod dependencies only, first run `just prodenv` and then
    # run `just run`.
    uv run --no-dev {{ args }}

# Run tests
test *args:
    uv run coverage run --source {{ justfile_directory() }} --module pytest {{ args }}
    uv run coverage report || uv run coverage html

# Fix code
fix *args=".":
    uv run ruff format {{ args }}
    uv run ruff check --fix {{ args }}

# Check code and lockfile
check *args=".":
    #!/usr/bin/env bash
    set -euo pipefail

    # The lockfile should be checked before `uv run` is used
    # Make sure dates in pyproject.toml and uv.lock are in sync
    unset UV_EXCLUDE_NEWER
    rc=0
    uv lock --check || rc=$?
    if test "$rc" != "0" ; then
        echo "Timestamp cutoffs in uv.lock must match those in pyproject.toml. See DEVELOPERS.md for details and hints." >&2
        exit $rc
    fi

    uv run ruff format --check {{ args }}
    uv run ruff check {{ args }}
    just docker/lint

# List the tasks
tasks-list: (run "python -m tasks list")

# Run a task
tasks-run task: (run "python -m tasks run" task)

# Run the Streamlit app
streamlit: (run "streamlit run app/app.py")

# Fetch the latest sanitised version of the OpenCodelists database
fetch-codelists-db:
    #!/usr/bin/env bash
    set -euo pipefail

    tmpdir="$(mktemp --directory)"
    cleanup() { rm --recursive --force "$tmpdir"; }
    trap cleanup EXIT

    remote_path=/var/lib/dokku/data/storage/opencodelists/backup/db/sanitised-latest-db.sqlite3.zst
    compressed_path="$tmpdir/sanitised-latest-db.sqlite3.zst"
    decompressed_path="$tmpdir/sanitised-latest-db.sqlite3"

    scp -q "$DOKKU_USERNAME@dokku3.ebmdatalab.net:$remote_path" "$compressed_path"
    zstd --decompress --quiet "$compressed_path" -o "$decompressed_path"
    mkdir --parents $(dirname $OPENCODELISTS_DATABASE_PATH)
    sqlite3 $OPENCODELISTS_DATABASE_PATH ".restore $decompressed_path"
