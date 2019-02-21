FROM python:2.7.15-slim

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
        make \
        netcat \
        python-dev \
        rsync \
        ruby-bundler \
        ruby-dev && \
    apt-get clean

COPY ./src/requirements /usr/src/app/requirements
COPY ./src/Gemfile /usr/src/app/Gemfile

RUN \
    pip install --no-cache-dir -r /usr/src/app/requirements/${mode}.txt && \
    cd /usr/src/app && \
    bundle install

COPY ./src /usr/src/app

RUN \
    mkdir -p /srv/app/media && \
    mkdir -p /srv/app/protected && \
    mkdir -p /srv/app/static && \
    chown -R www-data:www-data /usr/src/app /srv/app

RUN \
    cd /usr/src/app/phorum/static && \
    compass compile && \
    cd ../.. && \
    make collectstatic

WORKDIR "/srv/app"

VOLUME /srv/app/media
VOLUME /srv/app/protected
VOLUME /srv/app/static

COPY ./docker-entrypoint.sh /usr/local/bin

ENTRYPOINT ["docker-entrypoint.sh"]
