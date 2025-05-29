PYTHON := "python3.12"
VENV_DIR := ".venv"
BIN_DIR := VENV_DIR / "bin"
PIP := BIN_DIR / "python -m pip"
PIP_COMPILE := BIN_DIR / "pip-compile"
RUFF := BIN_DIR / "ruff"

# List available recipes and their arguments
default:
    @{{ just_executable() }} --list

# Remove the virtual environment
clean:
    rm -rf {{ VENV_DIR }}

# Create a virtual environment
venv:
    test -d {{ VENV_DIR }} || {{ PYTHON }} -m venv {{ VENV_DIR }} && {{ PIP }} install pip==25.0.1
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

_install env:
    #!/usr/bin/env bash
    set -euxo pipefail

    test requirements.{{ env }}.txt -nt {{ VENV_DIR }}/.{{ env }} || exit 0
    {{ PIP }} install -r requirements.{{ env }}.txt
    touch {{ VENV_DIR }}/.{{ env }}

# Install pre-commit hook
install-pre-commit:
    test -f .git/hooks/pre-commit || {{ BIN_DIR }}/pre-commit install

# Install prod requirements into the virtual environment
prodenv: requirements-prod (_install 'prod')

# Install dev requirements into the virtual environment
devenv: requirements-dev prodenv (_install 'dev') && install-pre-commit

# Run a command in the virtual environment
run *args: devenv
    echo "Not implemented"

# Run tests
test *args: devenv
    {{ BIN_DIR }}/coverage run --module pytest {{ args }}
    {{ BIN_DIR }}/coverage report

# Fix code
fix *args=".": devenv
    {{ RUFF }} format {{ args }}
    {{ RUFF }} check --fix {{ args }}

# Check code
check *args=".": devenv
    {{ RUFF }} check {{ args }}
