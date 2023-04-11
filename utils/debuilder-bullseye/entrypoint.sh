#!/bin/bash

set -o pipefail
set -o nounset
set -o errexit


restore_user() {
    current_user=$(stat . --format=%u)
    current_group=$(stat . --format=%g)
    find . -user root -exec chown $current_user:$current_group {} \;
}

trap restore_user EXIT

export DEBIAN_FRONTEND noninteractive
cd /src

apt-get \
    build-dep \
    --yes \
    --target-release bullseye-backports \
    .

debuild -uc -us

rm -rf build
mkdir build
mv ../*.deb build/
echo -e "\n\n###############################\nYour packages can be found now under:"
ls ./build/*
