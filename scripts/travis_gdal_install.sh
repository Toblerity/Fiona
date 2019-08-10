#!/bin/sh
set -e

# change back to travis build dir
cd $TRAVIS_BUILD_DIR


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
            --with-webp=no"

# Proj flag changed with gdal 2.3
if $(dpkg --compare-versions "$GDALVERSION" "lt" "2.3"); then
    GDALOPTS_PROJ="--with-static-proj4=$PROJINST/proj-$PROJVERSION";
else
    GDALOPTS_PROJ="--with-proj=${PROJINST}/proj-$PROJVERSION";
fi
            
# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

GDAL_DEB_PATH="gdal_${GDALVERSION}_proj_${PROJVERSION}-1_amd64_${DISTRIB_CODENAME}.deb"
if ( curl -o/dev/null -sfI "https://rbuffat.github.io/gdal_builder/$GDAL_DEB_PATH" ); then
  # install deb when available
  
  wget "https://rbuffat.github.io/gdal_builder/$GDAL_DEB_PATH"
  sudo dpkg -i "$GDAL_DEB_PATH"

elif [ ! -d "$GDALINST/gdal-$GDALVERSION" ]; then
  # only build if not already installed
  cd $GDALBUILD

  BASE_GDALVERSION=$(sed 's/[a-zA-Z].*//g' <<< $GDALVERSION)

  if ( curl -o/dev/null -sfI "http://download.osgeo.org/gdal/$BASE_GDALVERSION/gdal-$GDALVERSION.tar.gz" ); then
    wget http://download.osgeo.org/gdal/$BASE_GDALVERSION/gdal-$GDALVERSION.tar.gz
  else
    wget http://download.osgeo.org/gdal/old_releases/gdal-$GDALVERSION.tar.gz
  fi
  tar -xzf gdal-$GDALVERSION.tar.gz

  
  if [ -d "gdal-$BASE_GDALVERSION" ]; then
    cd gdal-$BASE_GDALVERSION
  elif [ -d "gdal-$GDALVERSION" ]; then
    cd gdal-$GDALVERSION
  fi
  
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $GDALOPTS_PROJ
  make -j 2
  make install
  rm -rf $GDALBUILD

elif [ "$GDALVERSION" = "master" ]; then
  # always rebuild master
  git clone -b master --single-branch --depth=1 https://github.com/OSGeo/gdal.git $GDALBUILD/master
  cd $GDALBUILD/master/gdal
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $GDALOPTS_PROJ
  make -j 2
  make install
  rm -rf $GDALBUILD
  
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
