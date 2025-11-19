# syntax=docker/dockerfile:1
# check=error=true
#################################################
#
# Images are structured as shown in this diagram:
# ┌──────────────────┐            ┌──────────────────┐
# │   base-python    ├────────────►     builder      │
# └────────┬─────────┘            └──────────┬───────┘
#          │                                 │
#          │                                 │COPY FROM
#          │     ┌──────────────────┐        │
#          └─────►   ethelred-prod  ◄────────┘
#                └──────────────────┘
# The goal of this stages structure is to minimise the size of the prod image by
# not including build dependencies.
#
#################################################
#
# Create base image with python installed.
# All Dockerfiles should start from the base-docker image

# These build args have defaults, but are usually set from docker/.env. They
# are used in FROM lines, so need to be declared globally and have defaults
# set.
ARG UBUNTU_VERSION=24.04
ARG UV_VERSION=0.9

# DL3007 ignored because base-docker we specifically always want to build on
# the latest base image, by design.
# hadolint ignore=DL3007
FROM ghcr.io/opensafely-core/base-action:${UBUNTU_VERSION} AS base-python

# We are going to use an apt cache on the host, so disable the default debian
# docker clean up that deletes that cache on every apt install
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Use deadsnakes ppa to install a fully working base python installation
# see: https://gist.github.com/tiran/2dec9e03c6f901814f6d1e8dad09528e
# Use space efficient utility from base image
RUN --mount=type=cache,target=/var/cache/apt <<'EOF'
UBUNTU_CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
KEY_PATH=/usr/share/keyrings/deadsnakes.asc
KEY_URL='https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf23c5a6cf475977595c89f51ba6932366a755776'
/usr/lib/apt/apt-helper download-file "$KEY_URL" "$KEY_PATH"
echo "deb [signed-by=$KEY_PATH] https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu ${UBUNTU_CODENAME} main" > /etc/apt/sources.list.d/deadsnakes-ppa.list
EOF

# Install the appropriate python version from deadsnakes
# NOTE: ensure .python-version is not excluded in .dockerignore
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=bind,source=.python-version,target=/.python-version \
    /root/docker-apt-install.sh "python$(cat /.python-version)"

# uv env var documentation: https://docs.astral.sh/uv/reference/environment/
# Copy files rather than symlink since the cache and the target are on different filesystems
ENV UV_LINK_MODE=copy
# Compile at installation time, not import time
ENV UV_COMPILE_BYTECODE=1
# We are providing python via deadsnakes ppa
# (as we require dynamic linking of openssl for security reasons)
ENV UV_PYTHON_DOWNLOADS=never
# Set the directory for the venv
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"

##################################################
#
# Reusable uv CLI layer
#
# This allows us to specify the version in one place, and also works around
# a limitation that you cannot use build args directly in `COPY --from`.
#
# See: https://github.com/moby/buildkit/issues/2412 for more info
#
#
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-cli

##################################################
#
# Build image
#
# Ok, now we have a local base image with python installed.
# We'll use this as the base for our builder image, where we'll build and
# install any python packages needed.
#
# We use a separate, disposable build image to avoid carrying the build
# dependencies into the production image.
FROM base-python AS builder

# Pull in the binaries from our pinned uv-cli stage
COPY --from=uv-cli /uv /uvx /usr/local/bin/

# Install everything in venv for isolation from system python libraries
RUN uv venv

# The cache mount means that /root/.cache is not in the image.
# Setting --directory /root lets `uv` detect the pyproject.toml, uv.lock etc.
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=pyproject.toml,target=/root/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/root/uv.lock \
    uv sync --frozen --no-dev --no-install-project --directory /root

##################################################
#
# Production image
#
# Ok, we've built everything we need, build an image with all dependencies and
# copy in the code.
#
# We expect the dependencies to change less often than the code, so we copy
# them in first to take advantage of docker layer caching.
FROM base-python AS ethelred-prod

RUN mkdir -p /ethelred
WORKDIR /ethelred
ENV VIRTUAL_ENV=/opt/venv/ \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/ethelred

# Copy venv over from builder image. These will have root:root ownership, but
# are readable by all.
COPY --from=builder /opt/venv /opt/venv

# Add metadata; note that the base-docker image already sets some basic metadata.
LABEL org.opencontainers.image.title="ethelred-streamlit-app" \
    org.opencontainers.image.description="Ethelred Streamlit app" \
    org.opencontainers.image.source="https://github.com/opensafely-core/ethelred"

# Copy application code except for things in .dockerignore
COPY . /ethelred

# Expose port for Streamlit
ARG STREAMLIT_SERVER_PORT
EXPOSE $STREAMLIT_SERVER_PORT

# Run the streamlit app
ENV STREAMLIT_SERVER_PORT=$STREAMLIT_SERVER_PORT
CMD ["streamlit", "run", "/ethelred/app/app.py"]

# Finally, tag with build information. These will change regularly, therefore
# we do them as the last action.
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.created=$BUILD_DATE
ARG GITREF=unknown
LABEL org.opencontainers.image.revision=$GITREF
