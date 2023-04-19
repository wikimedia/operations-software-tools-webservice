#!/bin/bash

set -o pipefail
set -o errexit


if [[ "${1}" == "--no-cache" ]]; then
    no_cache="--no-cache"
    shift
fi


distro="${1:-buster}"

docker build "utils/debuilder-${distro}" $no_cache -t "debuilder-${distro}:latest"
docker run --volume $PWD:/src:rw --rm "debuilder-${distro}:latest"
