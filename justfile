set dotenv-load := true

PYTHON := "python3.12"
VENV_DIR := ".venv"
BIN_DIR := VENV_DIR / "bin"
PIP := BIN_DIR / "python -m pip"
PIP_COMPILE := BIN_DIR / "pip-compile"
RUFF := BIN_DIR / "ruff"

# List available recipes and their arguments
default:
    @{{ just_executable() }} --list

# Check if a .env exists
_checkenv:
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ ! -f .env ]]; then
    # just will not pick up environment variables from a .env that it's just created,
    # and there isn't an easy way to load those into the environment, so we just
    # prompt the user to create a .env.
        echo "No '.env' file found; please create one from dotenv"
        exit 1
    fi

# Remove the virtual environment
clean:
    rm -rf {{ VENV_DIR }}

# Create a virtual environment
venv:
    test -d {{ VENV_DIR }} || {{ PYTHON }} -m venv {{ VENV_DIR }} && {{ PIP }} install --upgrade pip==25.2
    test -e {{ PIP_COMPILE }} || {{ PIP }} install pip-tools

_compile src dst *args: venv
    #!/usr/bin/env bash
    set -euxo pipefail

    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    {{ PIP_COMPILE }} --quiet --generate-hashes --resolver=backtracking --strip-extras --allow-unsafe --output-file={{ dst }} {{ src }} {{ args }}

# Compile prod requirements
requirements-prod *args: (_compile 'requirements.prod.in' 'requirements.prod.txt' args)

# Compile dev requirements
requirements-dev *args: requirements-prod (_compile 'requirements.dev.in' 'requirements.dev.txt' args)

# Upgrade the given dev or prod dependency, or all dependencies if no dependency is given
upgrade env package="": venv
    #!/usr/bin/env bash
    set -euxo pipefail

    if test -z "{{ package }}"; then
        opts='--upgrade';
    else
        opts="--upgrade-package {{ package }}";
    fi
    FORCE=true {{ just_executable() }} requirements-{{ env }} $opts

# Upgrade all dependencies (used by the update-dependencies GitHub Actions workflow)
update-dependencies:
    just upgrade prod
    just upgrade dev

_install env:
    #!/usr/bin/env bash
    set -euxo pipefail

    test requirements.{{ env }}.txt -nt {{ VENV_DIR }}/.{{ env }} || exit 0
    # We pass --no-deps to avoid using setuptools' deprecated interfaces.
    # https://pip.pypa.io/en/stable/topics/secure-installs/#do-not-use-setuptools-directly
    {{ PIP }} install --no-deps -r requirements.{{ env }}.txt
    touch {{ VENV_DIR }}/.{{ env }}

# Install pre-commit hook
install-pre-commit:
    test -f .git/hooks/pre-commit || {{ BIN_DIR }}/pre-commit install

# Install prod requirements into the virtual environment
prodenv: requirements-prod (_install 'prod')

# Install dev requirements into the virtual environment
devenv: requirements-dev prodenv (_install 'dev') && install-pre-commit

# Run a command
run *args: _checkenv prodenv
    {{ BIN_DIR }}/{{ args }}

# Run tests
test *args: devenv
    {{ BIN_DIR }}/coverage run --source {{ justfile_directory() }} --module pytest {{ args }}
    {{ BIN_DIR }}/coverage report || {{ BIN_DIR }}/coverage html

# Fix code
fix *args=".": devenv
    {{ RUFF }} format {{ args }}
    {{ RUFF }} check --fix {{ args }}

# Check code
check *args=".": devenv
    {{ RUFF }} format --check {{ args }}
    {{ RUFF }} check {{ args }}
