#!/bin/sh
set -ex
GDALDIR="${HOME}/gdalbuild"
CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.ncpu)

if [ ! -d "$GDALDIR" ]; then
  mkdir $GDALDIR;
fi

if [ "$GDALVERSION" = "1.11.2" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-1.11.2" ]; then
      wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz
      tar -xzvf gdal-1.11.2.tar.gz
    fi
    cd gdal-1.11.2
    ./configure --prefix=/usr --without-ogdi && make -j 2 && sudo make install
fi