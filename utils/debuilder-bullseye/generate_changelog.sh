#!/bin/bash

set -o pipefail
set -o nounset
set -o errexit

DEST_DISTRO=bullseye

restore_user() {
    current_user=$(stat . --format=%u)
    current_group=$(stat . --format=%g)
    find . -user root -exec chown $current_user:$current_group {} \;
}

trap restore_user EXIT

cd /src
git config --global --add safe.directory /src
echo "Updating changelog..."
EDITOR=true gbp dch -R

cur_version="$(dpkg-parsechangelog -S version)"

echo "Now you can send this patch for review,"\
    "remember to create a tag named 'debian/$cur_version' and push it when publishing the package."
