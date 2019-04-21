#!/bin/sh
set -e

# Create build dir if not exists
if [ ! -d "$PROJBUILD" ]; then
  mkdir $PROJBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

if [ ! -d "$GDALINST/proj-$PROJVERSION" ]; then
    cd $PROJBUILD

    wget http://download.osgeo.org/proj/proj-$PROJVERSION.tar.gz
    tar -xzf proj-$PROJVERSION.tar.gz
    cd proj-$PROJVERSION
    ./configure --prefix=$GDALINST/proj-$PROJVERSION
    make -j 2
    make install
    rm -rf $PROJBUILD
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
