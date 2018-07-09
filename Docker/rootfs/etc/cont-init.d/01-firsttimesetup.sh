#!/usr/bin/with-contenv bash

#if [ ! -f /config/removetoredoconf ]; then
    echo "First time set-up of automator"
    PUID=${PUID:-911}
    PGID=${PGID:-911}
    echo "PUID set to $PUID"
    echo "PGID set to $PGID"

    groupmod -o -g "$PGID" abc
    usermod -o -u "$PUID" abc
    git clone -b ${GITBRANCH} ${GITSERVER} /conversion-server
    cd /conversion-server && pip3 install -e .


    mkdir -p /var/log/server
    chown nobody:nogroup /var/log/server
    chown abc:abc -R /server
#    touch /config/removetoredoconf
#fi