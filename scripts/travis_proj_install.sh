#!/bin/sh
set -e

# Create build dir if not exists
if [ ! -d "$PROJBUILD" ]; then
  mkdir $PROJBUILD;
fi

<<<<<<< HEAD
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
=======
if [ ! -d "$PROJINST" ]; then
  mkdir $PROJINST;
fi

ls -l $PROJINST

echo "PROJ VERSION: $PROJVERSION"

if [ ! -d "$PROJINST/gdal-$GDALVERSION/share/proj" ]; then
    cd $PROJBUILD
    wget -q https://download.osgeo.org/proj/proj-$PROJVERSION.tar.gz
    tar -xzf proj-$PROJVERSION.tar.gz
    cd proj-$PROJVERSION
    ./configure --prefix=$PROJINST/gdal-$GDALVERSION
    make -s -j 2
    make install
>>>>>>> 1.8.10
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
