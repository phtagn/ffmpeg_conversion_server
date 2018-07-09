#!/usr/bin/with-contenv bash

if [ ${AUTOUPDATE} = true ]; then
    cd /server
    git checkout ${GITBRANCH} && git pull
fi