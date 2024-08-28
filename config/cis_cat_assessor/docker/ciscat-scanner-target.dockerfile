ARG TARGET_IMAGE
FROM ${TARGET_IMAGE}

USER root

RUN zypper ar --gpgcheck-strict -C -f https://arm.sero.gic.ericsson.se/artifactory/proj-ldc-repo-rpm-local/common_base_os/sles/3.44.0-9?ssl_verify=no LDC-CBO-SLES \
    && zypper --gpg-auto-import-keys refresh \
    && zypper install -l -y util-linux iproute2 \
    && zypper clean --all

ENTRYPOINT ["/usr/bin/catatonit"]