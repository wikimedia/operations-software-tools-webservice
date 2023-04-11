FROM debian:bullseye
ARG DEBIAN_FRONTEND noninteractive

COPY bullseye-backports.list /etc/apt/sources.list.d/
RUN apt update -y \
    && apt install -y ca-certificates

COPY toolforge.list /etc/apt/sources.list.d/

# git-buildpackage is to be able to generate the changelog
RUN apt update -y \
    && apt install -y \
        devscripts \
        git-buildpackage

COPY entrypoint.sh /entrypoint.sh
COPY generate_changelog.sh /generate_changelog.sh
ENTRYPOINT ["/entrypoint.sh"]
