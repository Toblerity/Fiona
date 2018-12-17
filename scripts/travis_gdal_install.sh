#!/bin/sh
set -e

GDALOPTS="  --with-ogr \
            --with-geos \
            --with-expat \
            --without-libtool \
            --with-libtiff=internal \
            --with-geotiff=internal \
            --without-gif \
            --without-pg \
            --without-grass \
            --without-libgrass \
            --without-cfitsio \
            --without-pcraster \
            --without-netcdf \
            --with-png=internal \
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
            --with-curl \
            --with-sqlite3 \
            --without-dwgdirect \
            --without-idb \
            --without-sde \
            --without-perl \
            --without-php \
            --without-ruby \
            --without-python
            --with-oci=no \
            --without-mrf \
            --without-lerc \
            --with-webp=no"

# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

if [ "$GDALVERSION" = "trunk" ]; then
  # always rebuild trunk
  git clone -b master --single-branch --depth=1 https://github.com/OSGeo/gdal.git $GDALBUILD/trunk
  cd $GDALBUILD/trunk/gdal
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS
  make -j 2
  make install
  rm -rf $GDALBUILD
  
elif [ ! -d "$GDALINST/gdal-$GDALVERSION" ]; then
  # only build if not already installed
  cd $GDALBUILD

  if ( curl -o/dev/null -sfI "http://download.osgeo.org/gdal/$GDALVERSION/gdal-$GDALVERSION.tar.gz" ); then
    wget http://download.osgeo.org/gdal/$GDALVERSION/gdal-$GDALVERSION.tar.gz
  else
    wget http://download.osgeo.org/gdal/old_releases/gdal-$GDALVERSION.tar.gz
  fi
  tar -xzf gdal-$GDALVERSION.tar.gz
  cd gdal-$GDALVERSION
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS
  make -j 2
  make install
  rm -rf $GDALBUILD
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
