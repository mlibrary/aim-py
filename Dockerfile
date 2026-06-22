################################################################################
# BASE                                                                         #
################################################################################
FROM python:3.14-slim-trixie@sha256:44dd04494ee8f3b538294360e7c4b3acb87c8268e4d0a4828a6500b1eff50061 AS base

ARG POETRY_VERSION=2.4.1
ARG UID=1000
ARG GID=1000
  

# Where python should look for packages and modules when using import
ENV PYTHONPATH="/app"

# Ensure the stdout and stderr streams are sent straight to terminal
ENV PYTHONUNBUFFERED=1 

# Turns off cache dir so it runs more quickly
ENV PIP_NO_CACHE_DIR=off 

# Speeds up pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=on 

ENV PIP_DEFAULT_TIMEOUT=100 

# Create our users here in the last layer or else it will be lost in the previous discarded layers
RUN groupadd -g ${GID} -o app
RUN useradd -m -d /app -u ${UID} -g ${GID} -o -s /bin/bash app

RUN apt-get update -yqq && apt-get install -yqq --no-install-recommends \
  python3-dev \ 
  default-libmysqlclient-dev \ 
  build-essential \ 
  pkg-config \
  default-mysql-client \
  vim-tiny \
  curl \ 
  zip \
  unzip

#get latest rclone because the apt version can't delete files on cifs
RUN curl https://rclone.org/install.sh | bash

# Set the working directory to /app
WORKDIR /app

CMD ["tail", "-f", "/dev/null"]

################################################################################
# POETRY
################################################################################
# Both build and development need poetry, so it is its own step.
FROM base AS poetry

RUN pip install poetry==${POETRY_VERSION}

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_KEYRING_ENABLED=false

# turning this off because it's making it so I can't install packages with poetry
#RUN poetry self add poetry-plugin-shell

################################################################################
# BUILD                                                                        #
################################################################################
FROM poetry AS build
# Just copy the files needed to install the dependencies
COPY pyproject.toml poetry.lock README.md ./

# Need to be able to export poetry
RUN poetry self add poetry-plugin-export

#Use poetry to create a requirements.txt file. Dont include development dependencies
RUN poetry export --without dev -f requirements.txt --output requirements.txt

################################################################################
# DEVELOPMENT                                                                  #
################################################################################
FROM poetry AS development
RUN apt-get update -yqq && apt-get install -yqq --no-install-recommends \
  git \
  bats \
  bats-assert \
  bats-file\
  wget

RUN wget -P /opt/ https://github.com/boschresearch/shellmock/releases/download/0.9.1/shellmock.bash && \
  chown ${UID}:${GID} /opt/shellmock.bash

ENV SHELLMOCK_PATH=/opt/shellmock.bash

# Switch to the non-root user "user"
USER app

################################################################################
# PRODUCTION                                                                   #
################################################################################
FROM base AS production
# Switch to the non-root user "user"
# RUN mkdir -p /venv && chown ${UID}:${GID} /venv


COPY --chown=${UID}:${GID} . /app
COPY --chown=${UID}:${GID} --from=build "/app/requirements.txt" /app/requirements.txt

RUN pip install -r /app/requirements.txt

USER app
