FROM quay.io/pypa/manylinux2014_x86_64:2024-04-15-dd44d68

# building openssl needs IPC-Cmd (https://github.com/microsoft/vcpkg/issues/24988)
RUN yum install -y curl unzip zip tar perl-IPC-Cmd

# require python >= 3.7 (python 3.6 is default on base image) for meson 
RUN ln -s /opt/python/cp38-cp38/bin/python3 /usr/bin/python3

RUN git clone https://github.com/Microsoft/vcpkg.git /opt/vcpkg && \
    git -C /opt/vcpkg checkout 2024.07.12

ENV VCPKG_INSTALLATION_ROOT="/opt/vcpkg"
ENV PATH="${PATH}:/opt/vcpkg"

ENV VCPKG_DEFAULT_TRIPLET="x64-linux-dynamic"

# mkdir & touch -> workaround for https://github.com/microsoft/vcpkg/issues/27786
RUN bootstrap-vcpkg.sh && \
    mkdir -p /root/.vcpkg/ $HOME/.vcpkg && \
    touch /root/.vcpkg/vcpkg.path.txt $HOME/.vcpkg/vcpkg.path.txt && \
    vcpkg integrate install && \
    vcpkg integrate bash

COPY ci/custom-triplets/x64-linux-dynamic.cmake opt/vcpkg/custom-triplets/x64-linux-dynamic.cmake
COPY ci/vcpkg-custom-ports/ opt/vcpkg/custom-ports/
COPY ci/vcpkg.json opt/vcpkg/

ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/vcpkg/installed/x64-linux-dynamic/lib"
RUN vcpkg install --overlay-triplets=opt/vcpkg/custom-triplets \
    --overlay-ports=opt/vcpkg/custom-ports \
    --feature-flags="versions,manifests" \
    --x-manifest-root=opt/vcpkg \
    --x-install-root=opt/vcpkg/installed && \
    vcpkg list

# setting git safe directory is required for properly building wheels when
# git >= 2.35.3
RUN git config --global --add safe.directory "*"
