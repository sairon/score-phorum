#!/bin/sh

run_as() {
    if [ "$(id -u)" = 0 ]; then
        su -p www-data -s /bin/sh -c "$1"
    else
        sh -c "$1"
    fi
}

if [ "$1" = "make" ]; then
    if [ "$(id -u)" = 0 ]; then
        rsync_options="-rlDog --chown www-data:www-data"
    else
        rsync_options="-rlD"
    fi

    rsync $rsync_options --delete --exclude /media --exclude /protected /usr/src/app/ /srv/app/

    for dir in media protected; do
        if [ ! -d "/srv/app/$dir" ] || [ -z "$(ls -A "/srv/app/$dir")" ]; then
            rsync $rsync_options --include "/$dir/" --exclude '/*' /usr/src/app/ /srv/app/
        fi
    done

    run_as "$@"
fi

for dir in media protected; do
    chown -R www-data:www-data "/srv/app/$dir"
done

exec "$@"
