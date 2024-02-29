ARG GDAL=ubuntu-small-3.6.4
FROM ghcr.io/osgeo/gdal:${GDAL} AS gdal
ARG PYTHON_VERSION=3.9
ENV LANG="C.UTF-8" LC_ALL="C.UTF-8"
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    g++ \
    gdb \
    make \
    python3-pip \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements*.txt ./
RUN python${PYTHON_VERSION} -m venv /venv && \
    /venv/bin/python -m pip install -U build pip && \
    /venv/bin/python -m pip install -r requirements-dev.txt && \
    /venv/bin/python -m pip list

FROM gdal
COPY . .
RUN /venv/bin/python -m build -o wheels
RUN /venv/bin/python -m pip install --no-index -f wheels fiona[test]
ENTRYPOINT ["/venv/bin/fio"]
CMD ["--help"]
