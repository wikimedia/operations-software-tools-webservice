#!/usr/bin/env bash

set -o errexit
set -o pipefail

if [[ "${1}" == "--no-cache" ]]; then
    no_cache="--no-cache"
    shift
fi

email="$(git config user.email)"
name="$(git config user.name)"
if [[ "${1}" == "buster" ]] || [[ "${1}" == "bullseye" ]]; then
    distro="${1}"
    shift
else
    distro="buster"
fi

docker build "utils/debuilder-${distro}" $no_cache -t "debuilder-${distro}:latest"
docker run \
    --entrypoint /generate_changelog.sh \
    --volume $PWD:/src:rw \
    --env "EMAIL=${email}" \
    --env "NAME=${name}" \
    --rm \
    "debuilder-${distro}:latest" \
    "$@"
