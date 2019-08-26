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
            --with-netcdf \
            --with-png=internal \
            --with-jpeg=internal \
            --without-gif \
            --without-ogdi \
            --without-fme \
            --without-hdf4 \
            --with-hdf5 \
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

# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

echo "GDAL VERSION: $GDALVERSION FORCE_GDAL_BUILD: $FORCE_GDAL_BUILD" 

GDAL_ARCHIVE_NAME="gdal_${GDALVERSION}_proj_${PROJVERSION}_${DISTRIB_CODENAME}.tar.gz"
GDAL_ARCHIVE_URL="https://rbuffat.github.io/gdal_builder/$GDAL_ARCHIVE_NAME"

echo "$GDAL_ARCHIVE_URL"

if ( curl -o/dev/null -sfI "$GDAL_ARCHIVE_URL" ) && [ "$FORCE_GDAL_BUILD" != "yes" ]; then
    echo "Use previously built gdal $GDALVERSION"
    
    wget "$GDAL_ARCHIVE_URL"
    
    echo "tar -xzvf $GDAL_ARCHIVE_NAME -C $GDALINST"
    tar -xzvf "$GDAL_ARCHIVE_NAME" -C "$GDALINST"

  
elif [ "$GDALVERSION" = "master" ]; then

    PROJOPT="--with-proj=$PROJINST/proj-$PROJVERSION"
    cd $GDALBUILD
    git clone --depth 1 https://github.com/OSGeo/gdal gdal-$GDALVERSION
    cd gdal-$GDALVERSION/gdal
    git rev-parse HEAD > newrev.txt
    BUILD=no
    # Only build if nothing cached or if the GDAL revision changed
    if test ! -f $GDALINST/gdal-$GDALVERSION/rev.txt; then
        BUILD=yes
    elif ! diff newrev.txt $GDALINST/gdal-$GDALVERSION/rev.txt >/dev/null; then
        BUILD=yes
    fi
    if test "$BUILD" = "yes"; then
        mkdir -p $GDALINST/gdal-$GDALVERSION
        cp newrev.txt $GDALINST/gdal-$GDALVERSION/rev.txt
        ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
        make -j 2
        make install
    fi

else

  BASE_GDALVERSION=$(sed 's/[a-zA-Z].*//g' <<< $GDALVERSION)
  
  # Proj flag changed with gdal 2.3
  if $(dpkg --compare-versions "$GDALVERSION" "lt" "2.3"); then
    PROJOPT="--with-static-proj4=$PROJINST/proj-$PROJVERSION";
  else
    PROJOPT="--with-proj=${PROJINST}/proj-$PROJVERSION";
  fi

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
  
  ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
  make -j 2
  make install
  rm -rf $GDALBUILD

fi

echo "Files in $GDALINST:"
find $GDALINST

echo $GDAL_DATA
ls -lh $GDAL_DATA
echo $PROJ_LIB
ls -lh $PROJ_LIB


# change back to travis build dir
cd $TRAVIS_BUILD_DIR
