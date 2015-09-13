#!/bin/sh
set -ex
GDALDIR="${HOME}/gdalbuild"

# Create build dir if not exists
if [ ! -d "$GDALDIR" ]; then
  mkdir $GDALDIR;
fi

# download and compile gdal version
if [ "$GDALVERSION" = "1.9.2" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-1.9.2" ]; then
      wget http://download.osgeo.org/gdal/gdal-1.9.2.tar.gz
      tar -xzvf gdal-1.9.2.tar.gz
    fi
    cd gdal-1.9.2
    ./configure --prefix=/usr --without-ogdi && make -j 2 && sudo make install
elif [ "$GDALVERSION" = "1.11.2" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-1.11.2" ]; then
      wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz
      tar -xzvf gdal-1.11.2.tar.gz
    fi
    cd gdal-1.11.2
    ./configure --prefix=/usr --without-ogdi && make -j 2 && sudo make install
elif [ "$GDALVERSION" = "2.0.0" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-2.0.0" ]; then
      wget http://download.osgeo.org/gdal/2.0.0/gdal-2.0.0.tar.gz
      tar -xzvf gdal-2.0.0.tar.gz
    fi
    cd gdal-2.0.0
    ./configure --prefix=/usr --without-ogdi && make -j 2 && sudo make install
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR