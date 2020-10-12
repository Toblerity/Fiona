#!/bin/bash
#
# originally contributed by @rbuffat to Toblerity/Fiona
set -e

GDALOPTS="  --with-geos \
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
            --without-openjpeg \
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
            --without-mysql \
            --without-ingres \
            --without-xerces \
            --without-odbc \
            --with-curl \
            --without-idb \
            --without-sde \
            --without-perl \
            --without-python \
            --with-oci=no \
            --without-mrf \
            --with-webp=no \
            --without-lerc"

# OS specific gdal build options
if [ $TRAVIS_OS_NAME = 'osx' ]; then
    GDALOPTS="$GDALOPTS \
                --with-expat=/usr/local/opt/expat \
                --with-sqlite3=/usr/local/opt/sqlite"
else
    GDALOPTS="$GDALOPTS \
              --with-expat \
              --with-sqlite3"
fi

if [ -d "$FILEGDB" ]; then
  GDALOPTS="$GDALOPTS --with-fgdb=$FILEGDB"
fi

# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

if [ "$GDALVERSION" = "master" ]; then
    PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
    cd $GDALBUILD
    git clone --depth 1 https://github.com/OSGeo/gdal gdal-$GDALVERSION
    cd gdal-$GDALVERSION/gdal
    echo $PROJVERSION > newproj.txt
    git rev-parse HEAD > newrev.txt
    BUILD=no
    # Only build if nothing cached or if the GDAL revision changed
    if test ! -f $GDALINST/gdal-$GDALVERSION/rev.txt; then
        BUILD=yes
    elif ( ! diff newrev.txt $GDALINST/gdal-$GDALVERSION/rev.txt >/dev/null ) || ( ! diff newproj.txt $GDALINST/gdal-$GDALVERSION/newproj.txt >/dev/null ); then
        BUILD=yes
    fi
    if test "$BUILD" = "yes"; then
        mkdir -p $GDALINST/gdal-$GDALVERSION
        cp newrev.txt $GDALINST/gdal-$GDALVERSION/rev.txt
        cp newproj.txt $GDALINST/gdal-$GDALVERSION/newproj.txt
        ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
        make
        make install
    fi

else

    PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"

    if [ ! -d "$GDALINST/gdal-$GDALVERSION/share/gdal" ]; then
        cd $GDALBUILD
        gdalver=$(expr "$GDALVERSION" : '\([0-9]*.[0-9]*.[0-9]*\)')
        wget -q http://download.osgeo.org/gdal/$gdalver/gdal-$GDALVERSION.tar.gz
        tar -xzf gdal-$GDALVERSION.tar.gz
        cd gdal-$gdalver
        ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
        make
        make install
    fi
fi

# Remove gdalbuild to emulate travis cache
rm -rf "$GDALBUILD"

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
