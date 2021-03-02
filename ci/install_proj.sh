#!/bin/sh

# Build and install PROJ on a POSIX system, save cache for later
#
# This script requires environment variables to be set
#  - export INSTALL_PREFIX=/path/to/cached/prefix -- to build or use as cache
#  - export PROJ_VERSION=6.3.0 or master -- to download and compile

set -e
# set -x

if [ -z "${INSTALL_PREFIX}" ]; then
    echo "INSTALL_PREFIX must be set"
    exit 1
elif [ -z "${PROJ_VERSION}" ]; then
    echo "PROJ_VERSION must be set"
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

# Create directories, if they don't exit
mkdir -p ${INSTALL_PREFIX}

# Download and build PROJ outside other source tree
PROJ_BUILD=$HOME/projbuild

prepare_proj_build_dir(){
  rm -rf $PROJ_BUILD
  mkdir -p $PROJ_BUILD
  cd $PROJ_BUILD
}

build_proj(){
    echo "Building proj-${PROJ_VERSION}"
    mkdir build
    cd build
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${INSTALL_PREFIX} ..
    make
    make install

    # Version-specific test options
    case ${PROJ_VERSION} in
        4.9.3)
            export PROJ_LIB=../nad
            ;;
        5.*)
            export PROJ_LIB=../nad
            ;;
        6.*)
            export PROJ_LIB=${INSTALL_PREFIX}/share/proj
            (cd data && unzip -o ../../data/proj-datumgrid-1.8.zip)
            ;;
#    else
#        unset PROJ_LIB
    esac

    ctest --output-on-failure
}

if [ "${PROJ_VERSION}" = "master" ]; then
    prepare_proj_build_dir
    # use GitHub
    git clone --depth 1 https://github.com/OSGeo/PROJ.git proj-${PROJ_VERSION}
    cd proj-${PROJ_VERSION}
    git rev-parse HEAD > new_proj.rev
    BUILD=no
    # Only build if nothing cached or if the PROJ revision changed
    if test ! -f ${INSTALL_PREFIX}/proj.rev; then
        BUILD=yes
    elif ! diff new_proj.rev ${INSTALL_PREFIX}/proj.rev >/dev/null; then
        BUILD=yes
    fi
    if test "$BUILD" = "no"; then
        echo "Using cached install of PROJ in ${INSTALL_PREFIX}"
    else
        # force any rebuild of GDAL
        rm -f ${INSTALL_PREFIX}/gdal.rev
        build_proj
        cp new_proj.rev ${INSTALL_PREFIX}/proj.rev
    fi
else
    if [ -d "${INSTALL_PREFIX}/include/proj" ]; then
        echo "Using cached install of PROJ in ${INSTALL_PREFIX}"
    else
        prepare_proj_build_dir
        wget -q -nc http://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
        tar xfz proj-${PROJ_VERSION}.tar.gz
        cd proj-${PROJ_VERSION}

        # Version-specific configure options
        case ${PROJ_VERSION} in
            5.*)
                cd nad
                wget -q -nc http://download.osgeo.org/proj/proj-datumgrid-1.7.zip
                unzip -o proj-datumgrid-1.7.zip
                cd ..
                ;;
            6.*)
                cd data
                wget -q -nc http://download.osgeo.org/proj/proj-datumgrid-1.8.zip
                unzip -o proj-datumgrid-1.8.zip
                cd ..
                ;;
        esac
        build_proj
    fi
fi
