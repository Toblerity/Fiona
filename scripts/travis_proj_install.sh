#!/bin/sh
set -e

# change back to travis build dir
cd $TRAVIS_BUILD_DIR

# Create build dir if not exists
if [ ! -d "$PROJBUILD" ]; then
    mkdir $PROJBUILD;
fi

if [ ! -d "$PROJINST" ]; then
    mkdir $PROJINST;
fi

echo "PROJ VERSION: $PROJVERSION FORCE_GDAL_BUILD: $FORCE_GDAL_BUILD" 

PROJ_ARCHIVE_NAME="proj_${PROJVERSION}_${DISTRIB_CODENAME}.tar.gz"
PROJ_ARCHIVE_URL="https://rbuffat.github.io/gdal_builder/$PROJ_ARCHIVE_NAME"

echo "$PROJ_ARCHIVE_URL"

if ( curl -o/dev/null -sfI "$PROJ_ARCHIVE_URL" ) && [ "$FORCE_GDAL_BUILD" != "yes" ]; then

    echo "Use previously built proj $PROJVERSION"
    
    wget "$PROJ_ARCHIVE_URL"
    
    echo "tar -xzvf $PROJ_ARCHIVE_NAME -C $PROJINST"
    tar -xzvf "$PROJ_ARCHIVE_NAME" -C "$PROJINST"

else
# Otherwise we compile proj from source

    if [ ! -d "$PROJINST/proj-$PROJVERSION" ]; then
        cd $PROJBUILD

        wget -q http://download.osgeo.org/proj/proj-$PROJVERSION.tar.gz
        tar -xzf proj-$PROJVERSION.tar.gz
        cd proj-$PROJVERSION
        ./configure --prefix=$PROJINST/proj-$PROJVERSION
        make -j 2
        make install
        rm -rf $PROJBUILD
    fi

fi

echo "Files in $PROJINST:"
find $PROJINST

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
