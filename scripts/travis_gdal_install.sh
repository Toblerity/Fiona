#!/bin/sh
set -e

GDALOPTS="  --with-ogr \
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
            --with-png=/usr \
            --with-jpeg=internal \
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
            --without-idb \
            --without-sde \
            --without-perl \
            --without-php \
            --without-ruby \
            --without-python"

# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

if [ "$GDALVERSION" = "1.9.2" -a ! -d "$GDALINST/gdal-$GDALVERSION" ]; then
  cd $GDALBUILD
  wget http://download.osgeo.org/gdal/gdal-$GDALVERSION.tar.gz
  tar -xzf gdal-$GDALVERSION.tar.gz
  cd gdal-$GDALVERSION
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS
  make -s -j 2
  make install
fi


# download and compile gdal version
if [ "$GDALVERSION" != "1.9.2" -a ! -d "$GDALINST/gdal-$GDALVERSION" ]; then
  cd $GDALBUILD
  wget http://download.osgeo.org/gdal/$GDALVERSION/gdal-$GDALVERSION.tar.gz
  tar -xzf gdal-$GDALVERSION.tar.gz
  cd gdal-$GDALVERSION
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS
  make -s -j 2
  make install
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
