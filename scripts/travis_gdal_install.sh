#!/bin/sh
set -ex
GDALDIR="${HOME}/gdalbuild"

GDALOPTS="--prefix=/usr --with-ogr \
            --with-geos \
            --with-expat \
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
            --without-png \
            --without-jpeg \
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
            --without-bsb \
            --without-grib \
            --without-mysql \
            --without-ingres \
            --without-xerces \
            --without-odbc \
            --without-curl \
            --without-sqlite3 \
            --without-dwgdirect \
            --without-panorama \
            --without-idb \
            --without-sde \
            --without-perl \
            --without-php \
            --without-ruby \
            --without-python \
            --without-ogpython"

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
    ./configure $GDALOPTS && make -j 2 && sudo make install
elif [ "$GDALVERSION" = "1.11.2" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-1.11.2" ]; then
      wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz
      tar -xzvf gdal-1.11.2.tar.gz
    fi
    cd gdal-1.11.2
    ./configure $GDALOPTS && make -j 2 && sudo make install
elif [ "$GDALVERSION" = "2.0.0" ]; then
    cd $GDALDIR
    if [ ! -d "$GDALDIR/gdal-2.0.0" ]; then
      wget http://download.osgeo.org/gdal/2.0.0/gdal-2.0.0.tar.gz
      tar -xzvf gdal-2.0.0.tar.gz
    fi
    cd gdal-2.0.0
    ./configure $GDALOPTS && make -j 2 && sudo make install
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
