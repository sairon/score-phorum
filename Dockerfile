# Sass -> CSS build
FROM ruby:3.4.5-slim AS sass

COPY ./src/phorum/static /usr/src/app/phorum/static

RUN \
    --mount=type=bind,source=./src/Gemfile,target=/usr/src/app/Gemfile \
    cd /usr/src/app/ && \
    apt-get update && \
    apt-get install -y git && \
    bundle install && \
    cd /usr/src/app/phorum/static && \
    bundle exec compass compile

# Python build
FROM python:3.13.5-slim AS build

ARG mode=production

ENV \
    DJANGO_SETTINGS_MODULE=score.settings.${mode} \
    PHORUM_DB_HOST=postgres \
    PHORUM_DB_NAME=score \
    PHORUM_DB_USER=score \
    PHORUM_DB_PASSWORD=score \
    PHORUM_SECRET_KEY=dummy \
    PHORUM_EMAIL_HOST=smtp

RUN \
    apt-get update && \
    apt-get install -y \
        libfreetype6-dev \
        gcc \
        libjpeg-dev \
        libffi-dev \
        libpng-dev \
        make && \
    apt-get clean

COPY ./src/requirements /usr/src/app/requirements

RUN \
    pip install --no-cache-dir -r /usr/src/app/requirements/${mode}.txt && \
    cd /usr/src/app

COPY ./src /usr/src/app

RUN \
    mkdir -p /srv/app/media && \
    mkdir -p /srv/app/protected && \
    mkdir -p /srv/app/static && \
    chown -R www-data:www-data /usr/src/app /srv/app

COPY --from=sass /usr/src/app/phorum/static /usr/src/app/phorum/static

RUN \
    cd /usr/src/app/ && \
    make collectstatic

# Final image
FROM python:3.13.5-slim

ARG mode=production

ENV \
    DJANGO_SETTINGS_MODULE=score.settings.${mode} \
    PHORUM_DB_HOST=postgres \
    PHORUM_DB_NAME=score \
    PHORUM_DB_USER=score \
    PHORUM_DB_PASSWORD=score \
    PHORUM_SECRET_KEY=dummy \
    PHORUM_EMAIL_HOST=smtp

RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y \
        make \
        netcat-traditional \
        rsync && \
    apt-get clean

WORKDIR "/srv/app"

VOLUME ["/srv/app/media", "/srv/app/protected", "/srv/app/static"]

COPY ./docker-entrypoint.sh /usr/local/bin

COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/src/app /usr/src/app

ENTRYPOINT ["docker-entrypoint.sh"]
