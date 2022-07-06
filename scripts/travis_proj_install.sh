#!/bin/sh
set -e

# Create build dir if not exists
if [ ! -d "$PROJBUILD" ]; then
    mkdir $PROJBUILD;
fi

if [ ! -d "$PROJINST" ]; then
    mkdir $PROJINST;
fi

ls -l $PROJINST

echo "PROJ VERSION: $PROJVERSION"

if [ ! -d "$PROJINST/gdal-$GDALVERSION/share/proj" ]; then
    cd $PROJBUILD
    wget -q https://download.osgeo.org/proj/proj-$PROJVERSION.tar.gz
    tar -xzf proj-$PROJVERSION.tar.gz
    projver=$(expr "$PROJVERSION" : '\([0-9]*.[0-9]*.[0-9]*\)')
    cd proj-$projver
    if [ -f "configure" ]; then
        ./configure --prefix=$PROJINST/gdal-$GDALVERSION
        make -s
        make install
    else
        cmake . -DCMAKE_PREFIX_PATH=$PROJINST/gdal-$GDALVERSION -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
        make -s
        make install
    fi
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
