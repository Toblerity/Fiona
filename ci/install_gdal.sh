#!/bin/sh

# Build and install GDAL on a POSIX system, save cache for later
#
# This script requires environment variables to be set
#  - export INSTALL_PREFIX=/path/to/cached/prefix -- to build or use as cache
#  - export GDAL_VERSION=3.0.4 or master -- to download and compile

set -e
# set -x

if [ -z "${INSTALL_PREFIX}" ]; then
    echo "INSTALL_PREFIX must be set"
    exit 1
elif [ -z "${GDAL_VERSION}" ]; then
    echo "GDAL_VERSION must be set"
    exit 1
fi

NPROC=2
UNAME="$(uname)" || UNAME=""
case ${UNAME} in
    Linux)
        NPROC=$(nproc) ;;
    Darwin)
        NPROC=$(sysctl -n hw.ncpu) ;;
esac
export MAKEFLAGS="-j ${NPROC}"

GDAL_OPTS="--enable-static=no \
    --with-proj=${INSTALL_PREFIX} \
    --with-curl \
    --with-geos \
    --without-libtool \
    --with-libz=internal \
    --with-libtiff=internal \
    --with-geotiff=internal \
    --without-gif \
    --without-pg \
    --without-grass \
    --without-libgrass \
    --without-cfitsio \
    --without-pcraster \
    --without-netcdf \
    --without-openjpeg \
    --without-gif \
    --without-ogdi \
    --without-fme \
    --without-hdf4 \
    --without-hdf5 \
    --without-jasper \
    --without-ecw \
    --without-kakadu \
    --without-mrsid \
    --without-jp2mrsid \
    --without-mysql \
    --without-ingres \
    --without-xerces \
    --without-odbc \
    --without-idb \
    --without-perl \
    --without-python \
    --with-oci=no \
    --with-webp=no"

# Version specific gdal build options
case ${GDAL_VERSION} in
    2.3*)
        GDAL_OPTS="${GDAL_OPTS} \
        --without-php \
        --without-bsb \
        --without-mrf \
        --without-grib \
        --without-png \
        --without-jpeg" ;;
    2.4*)
        GDAL_OPTS="${GDAL_OPTS} \
        --without-bsb \
        --without-mrf \
        --without-grib \
        --without-lerc \
        --without-png \
        --without-jpeg" ;;
    3*)
        GDAL_OPTS="${GDAL_OPTS} \
        --without-lerc \
        --with-png=internal \
        --with-jpeg=internal" ;;
    *)
        GDAL_OPTS="${GDAL_OPTS} \
        --without-lerc \
        --with-png=internal \
        --with-jpeg=internal" ;;
esac

# OS specific gdal build options
case ${UNAME} in
    Linux)
        GDAL_OPTS="${GDAL_OPTS} \
        --with-expat \
        --with-sqlite3" ;;
    Darwin)
        GDAL_OPTS="${GDAL_OPTS} \
        --with-expat=/usr/local/opt/expat \
        --with-sqlite3=/usr/local/opt/sqlite" ;;
esac

# Strip whitespace
GDAL_OPTS=$(echo $GDAL_OPTS | tr -s " ")

# Download and build GDAL outside other source tree
GDAL_BUILD=$HOME/gdalbuild

prepare_gdal_build_dir(){
  rm -rf $GDAL_BUILD
  mkdir -p $GDAL_BUILD
  cd $GDAL_BUILD
}

build_gdal(){
    echo "Building gdal-${GDAL_VERSION}"
    echo "./configure --prefix=${INSTALL_PREFIX} ${GDAL_OPTS}"
    ./configure --prefix=${INSTALL_PREFIX} ${GDAL_OPTS}
    make
    make install
}

if [ "${GDAL_VERSION}" = "master" ]; then
    prepare_gdal_build_dir
    # use GitHub
    git clone --depth 1 https://github.com/OSGeo/gdal.git gdal-${GDAL_VERSION}
    cd gdal-${GDAL_VERSION}/gdal
    git rev-parse HEAD > new_gdal.rev
    BUILD=no
    # Only build if nothing cached or if the GDAL revision changed
    if test ! -f ${INSTALL_PREFIX}/gdal.rev; then
        BUILD=yes
    elif ! diff new_gdal.rev ${INSTALL_PREFIX}/gdal.rev >/dev/null; then
        BUILD=yes
    fi
    if test "$BUILD" = "no"; then
        echo "Using cached install of GDAL in ${INSTALL_PREFIX}"
    else
        ./autogen.sh
        build_gdal
        cp new_gdal.rev ${INSTALL_PREFIX}/gdal.rev
    fi
else
    if [ -d "${INSTALL_PREFIX}/include/gdal" ]; then
        echo "Using cached install of GDAL in ${INSTALL_PREFIX}"
    else
        prepare_gdal_build_dir
        wget -q -nc http://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz
        tar xfz gdal-${GDAL_VERSION}.tar.gz
        cd gdal-${GDAL_VERSION}
        build_gdal
    fi
fi
