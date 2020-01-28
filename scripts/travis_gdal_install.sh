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
            --with-webp=no"

# Version specific gdal build options
case "$GDALVERSION" in
    2.3*)
        GDALOPTS="$GDALOPTS \
        --without-php \
        --without-bsb \
        --without-mrf \
        --without-grib \
        --without-png \
        --without-jpeg"
        ;;
    2.4*)
        GDALOPTS="$GDALOPTS \
        --without-bsb \
        --without-mrf \
        --without-grib \
        --without-lerc \
        --without-png \
        --without-jpeg"
        ;;
    3*)
        GDALOPTS="$GDALOPTS \
        --without-lerc \
        --with-png=internal \
        --with-jpeg=internal"
        ;;
    *)
        GDALOPTS="$GDALOPTS \
        --without-lerc \
        --with-png=internal \
        --with-jpeg=internal"
        ;;
esac

# OS specific gdal build options
if [ "$TRAVIS_OS_NAME" = "linux" ]; then

    GDALOPTS="$GDALOPTS \
                --with-expat \
                --with-sqlite3"

elif [ $TRAVIS_OS_NAME = 'osx' ]; then

    GDALOPTS="$GDALOPTS \
                --with-expat=/usr/local/opt/expat \
                --with-sqlite3=/usr/local/opt/sqlite"
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
        echo "./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT"
        ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
        make
        make install
    fi

else

    case "$GDALVERSION" in
        3*)
            PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
            ;;
        2.4*)
            PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
            ;;
        2.3*)
            PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
            ;;
        *)
            PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
            ;;
    esac

    if [ ! -d "$GDALINST/gdal-$GDALVERSION/share/gdal" ]; then
        cd $GDALBUILD
        gdalver=$(expr "$GDALVERSION" : '\([0-9]*.[0-9]*.[0-9]*\)')
        wget -q http://download.osgeo.org/gdal/$gdalver/gdal-$GDALVERSION.tar.gz
        tar -xzf gdal-$GDALVERSION.tar.gz
        cd gdal-$gdalver
        echo "./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT"
        ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
        make
        make install
    fi
fi

# Remove gdalbuild to emulate travis cache
rm -rf $GDALBUILD

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
