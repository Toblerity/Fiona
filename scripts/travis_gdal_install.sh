#!/bin/bash
#
# originally contributed by @rbuffat to Toblerity/Fiona
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
            --without-idb \
            --without-sde \
            --without-ruby \
            --without-perl \
            --without-php \
            --without-python \
            --with-oci=no \
            --without-mrf \
            --with-webp=no"

GDAL_CMAKE_OPTS=" -DBUILD_APPS=OFF \
        -DBUILD_CSHARP_BINDINGS=OFF \
        -DBUILD_JAVA_BINDINGS=OFF \
        -DBUILD_PYTHON_BINDINGS=OFF \
        -DGDAL_USE_MSSQL_NCLI=OFF \
        -DGDAL_USE_MSSQL_ODBC=OFF \
        -DGDAL_BUILD_OPTIONAL_DRIVERS=OFF \
        -DGDAL_ENABLE_DRIVER_AAIGRID=OFF \
        -DGDAL_ENABLE_DRIVER_ADRG=OFF \
        -DGDAL_ENABLE_DRIVER_AIRSAR=OFF \
        -DGDAL_ENABLE_DRIVER_ARG=OFF \
        -DGDAL_ENABLE_DRIVER_BLX=OFF \
        -DGDAL_ENABLE_DRIVER_BMP=OFF \
        -DGDAL_ENABLE_DRIVER_BSB=OFF \
        -DGDAL_ENABLE_DRIVER_CALS=OFF \
        -DGDAL_ENABLE_DRIVER_CEOS=OFF \
        -DGDAL_ENABLE_DRIVER_COASP=OFF \
        -DGDAL_ENABLE_DRIVER_COSAR=OFF \
        -DGDAL_ENABLE_DRIVER_CTG=OFF \
        -DGDAL_ENABLE_DRIVER_DAAS=OFF \
        -DGDAL_ENABLE_DRIVER_DIMAP=OFF \
        -DGDAL_ENABLE_DRIVER_DTED=OFF \
        -DGDAL_ENABLE_DRIVER_EEDA=OFF \
        -DGDAL_ENABLE_DRIVER_ELAS=OFF \
        -DGDAL_ENABLE_DRIVER_ENVISAT=OFF \
        -DGDAL_ENABLE_DRIVER_ERS=OFF \
        -DGDAL_ENABLE_DRIVER_ESRIC=OFF \
        -DGDAL_ENABLE_DRIVER_EXR=OFF \
        -DGDAL_ENABLE_DRIVER_FIT=OFF \
        -DGDAL_ENABLE_DRIVER_FITS=OFF \
        -DGDAL_ENABLE_DRIVER_GFF=OFF \
        -DGDAL_ENABLE_DRIVER_GIF=OFF \
        -DGDAL_ENABLE_DRIVER_GRIB=OFF \
        -DGDAL_ENABLE_DRIVER_GSG=OFF \
        -DGDAL_ENABLE_DRIVER_GTIFF=OFF \
        -DGDAL_ENABLE_DRIVER_GXF=OFF \
        -DGDAL_ENABLE_DRIVER_HDF5=OFF \
        -DGDAL_ENABLE_DRIVER_HEIF=OFF \
        -DGDAL_ENABLE_DRIVER_HF2=OFF \
        -DGDAL_ENABLE_DRIVER_HFA=OFF \
        -DGDAL_ENABLE_DRIVER_HTTP=OFF \
        -DGDAL_ENABLE_DRIVER_IDRISI=ON \
        -DGDAL_ENABLE_DRIVER_ILWIS=OFF \
        -DGDAL_ENABLE_DRIVER_IRIS=OFF \
        -DGDAL_ENABLE_DRIVER_JAXAPALSAR=OFF \
        -DGDAL_ENABLE_DRIVER_JDEM=OFF \
        -DGDAL_ENABLE_DRIVER_JP2OPENJPEG=OFF \
        -DGDAL_ENABLE_DRIVER_JPEG=OFF \
        -DGDAL_ENABLE_DRIVER_KMLSUPEROVERLAY=OFF \
        -DGDAL_ENABLE_DRIVER_L1B=OFF \
        -DGDAL_ENABLE_DRIVER_LEVELLER=OFF \
        -DGDAL_ENABLE_DRIVER_MAP=OFF \
        -DGDAL_ENABLE_DRIVER_MBTILES=OFF \
        -DGDAL_ENABLE_DRIVER_MEM=OFF \
        -DGDAL_ENABLE_DRIVER_MRF=OFF \
        -DGDAL_ENABLE_DRIVER_MSGN=OFF \
        -DGDAL_ENABLE_DRIVER_NETCDF=OFF \
        -DGDAL_ENABLE_DRIVER_NGSGEOID=OFF \
        -DGDAL_ENABLE_DRIVER_NITF=OFF \
        -DGDAL_ENABLE_DRIVER_NORTHWOOD=OFF \
        -DGDAL_ENABLE_DRIVER_OGCAPI=OFF \
        -DGDAL_ENABLE_DRIVER_OZI=OFF \
        -DGDAL_ENABLE_DRIVER_PCIDSK=ON \
        -DGDAL_ENABLE_DRIVER_PCRASTER=OFF \
        -DGDAL_ENABLE_DRIVER_PDF=OFF \
        -DGDAL_ENABLE_DRIVER_PDS=ON \
        -DGDAL_ENABLE_DRIVER_PLMOSAIC=OFF \
        -DGDAL_ENABLE_DRIVER_PNG=OFF \
        -DGDAL_ENABLE_DRIVER_POSTGISRASTER=OFF \
        -DGDAL_ENABLE_DRIVER_PRF=OFF \
        -DGDAL_ENABLE_DRIVER_R=OFF \
        -DGDAL_ENABLE_DRIVER_RASTERLITE=OFF \
        -DGDAL_ENABLE_DRIVER_RAW=OFF \
        -DGDAL_ENABLE_DRIVER_RIK=OFF \
        -DGDAL_ENABLE_DRIVER_RMF=OFF \
        -DGDAL_ENABLE_DRIVER_RS2=OFF \
        -DGDAL_ENABLE_DRIVER_SAFE=OFF \
        -DGDAL_ENABLE_DRIVER_SAGA=OFF \
        -DGDAL_ENABLE_DRIVER_SAR_CEOS=OFF \
        -DGDAL_ENABLE_DRIVER_SDTS=OFF \
        -DGDAL_ENABLE_DRIVER_SENTINEL2=OFF \
        -DGDAL_ENABLE_DRIVER_SGI=OFF \
        -DGDAL_ENABLE_DRIVER_SIGDEM=OFF \
        -DGDAL_ENABLE_DRIVER_SRTMHGT=OFF \
        -DGDAL_ENABLE_DRIVER_STACIT=OFF \
        -DGDAL_ENABLE_DRIVER_STACTA=OFF \
        -DGDAL_ENABLE_DRIVER_TERRAGEN=OFF \
        -DGDAL_ENABLE_DRIVER_TGA=OFF \
        -DGDAL_ENABLE_DRIVER_TIL=OFF \
        -DGDAL_ENABLE_DRIVER_TSX=OFF \
        -DGDAL_ENABLE_DRIVER_USGSDEM=OFF \
        -DGDAL_ENABLE_DRIVER_VRT=OFF \
        -DGDAL_ENABLE_DRIVER_WCS=OFF \
        -DGDAL_ENABLE_DRIVER_WEBP=OFF \
        -DGDAL_ENABLE_DRIVER_WMS=OFF \
        -DGDAL_ENABLE_DRIVER_WMTS=OFF \
        -DGDAL_ENABLE_DRIVER_XPM=OFF \
        -DGDAL_ENABLE_DRIVER_XYZ=OFF \
        -DGDAL_ENABLE_DRIVER_ZARR=OFF \
        -DGDAL_ENABLE_DRIVER_ZMAP=OFF \
        -DOGR_BUILD_OPTIONAL_DRIVERS=OFF \
        -DOGR_ENABLE_DRIVER_AVC=OFF \
        -DOGR_ENABLE_DRIVER_CAD=OFF \
        -DOGR_ENABLE_DRIVER_CSV=ON \
        -DOGR_ENABLE_DRIVER_CSW=OFF \
        -DOGR_ENABLE_DRIVER_DGN=ON \
        -DOGR_ENABLE_DRIVER_DXF=ON \
        -DOGR_ENABLE_DRIVER_EDIGEO=OFF \
        -DOGR_ENABLE_DRIVER_ELASTIC=OFF \
        -DOGR_ENABLE_DRIVER_FLATGEOBUF=ON \
        -DOGR_ENABLE_DRIVER_GEOCONCEPT=OFF \
        -DOGR_ENABLE_DRIVER_GEOJSON=ON \
        -DOGR_ENABLE_DRIVER_GEORSS=OFF \
        -DOGR_ENABLE_DRIVER_GML=ON \
        -DOGR_ENABLE_DRIVER_GMT=ON \
        -DOGR_ENABLE_DRIVER_GPKG=ON \
        -DOGR_ENABLE_DRIVER_GPSBABEL=OFF \
        -DOGR_ENABLE_DRIVER_GPX=ON \
        -DOGR_ENABLE_DRIVER_IDRISI=OFF \
        -DOGR_ENABLE_DRIVER_ILI=OFF \
        -DOGR_ENABLE_DRIVER_JML=OFF \
        -DOGR_ENABLE_DRIVER_KML=OFF \
        -DOGR_ENABLE_DRIVER_LIBKML=OFF \
        -DOGR_ENABLE_DRIVER_LVBAG=OFF \
        -DOGR_ENABLE_DRIVER_MAPML=OFF \
        -DOGR_ENABLE_DRIVER_MEM=OFF \
        -DOGR_ENABLE_DRIVER_MSSQLSPATIAL=OFF \
        -DOGR_ENABLE_DRIVER_MYSQL=OFF \
        -DOGR_ENABLE_DRIVER_NAS=OFF \
        -DOGR_ENABLE_DRIVER_NGW=OFF \
        -DOGR_ENABLE_DRIVER_NTF=OFF \
        -DOGR_ENABLE_DRIVER_ODBC=OFF \
        -DOGR_ENABLE_DRIVER_ODS=OFF \
        -DOGR_ENABLE_DRIVER_OPENFILEGDB=ON \
        -DOGR_ENABLE_DRIVER_OSM=OFF \
        -DOGR_ENABLE_DRIVER_PGDUMP=OFF \
        -DOGR_ENABLE_DRIVER_PGEO=OFF \
        -DOGR_ENABLE_DRIVER_PLSCENES=OFF \
        -DOGR_ENABLE_DRIVER_S57=ON \
        -DOGR_ENABLE_DRIVER_SDTS=OFF \
        -DOGR_ENABLE_DRIVER_SELAFIN=OFF \
        -DOGR_ENABLE_DRIVER_SHAPE=ON \
        -DOGR_ENABLE_DRIVER_SQLITE=ON \
        -DOGR_ENABLE_DRIVER_SVG=OFF \
        -DOGR_ENABLE_DRIVER_SXF=OFF \
        -DOGR_ENABLE_DRIVER_TAB=ON \
        -DOGR_ENABLE_DRIVER_TIGER=OFF \
        -DOGR_ENABLE_DRIVER_VDV=OFF \
        -DOGR_ENABLE_DRIVER_VFK=OFF \
        -DOGR_ENABLE_DRIVER_VRT=ON \
        -DOGR_ENABLE_DRIVER_WASP=OFF \
        -DOGR_ENABLE_DRIVER_WFS=OFF \
        -DOGR_ENABLE_DRIVER_XLS=OFF \
        -DOGR_ENABLE_DRIVER_XLSX=OFF "

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
    cd gdal-$GDALVERSION
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
        mkdir build
        cd build
        echo "cmake -DCMAKE_INSTALL_PREFIX=$GDALINST/gdal-$GDALVERSION -DPROJ_INCLUDE_DIR=$GDALINST/gdal-$GDALVERSION $GDAL_CMAKE_OPTS -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF .."
        cmake -DCMAKE_INSTALL_PREFIX=$GDALINST/gdal-$GDALVERSION "-DPROJ_INCLUDE_DIR=$GDALINST/gdal-$GDALVERSION" $GDAL_CMAKE_OPTS -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF ..
        cmake --build .
        cmake --build . --target install
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
        2.2*)
            PROJOPT="--with-static-proj4=$GDALINST/gdal-$GDALVERSION"
            ;;
        2.1*)
            PROJOPT="--with-static-proj4=$GDALINST/gdal-$GDALVERSION"
            ;;
        2.0*)
            PROJOPT="--with-static-proj4=$GDALINST/gdal-$GDALVERSION"
            ;;
        1*)
            PROJOPT="--with-static-proj4=$GDALINST/gdal-$GDALVERSION"
            ;;
        *)
            PROJOPT="--with-proj=$GDALINST/gdal-$GDALVERSION"
            ;;
    esac

    if [ ! -d "$GDALINST/gdal-$GDALVERSION/share/gdal" ]; then
        cd $GDALBUILD
        gdalver=$(expr "$GDALVERSION" : '\([0-9]*.[0-9]*.[0-9]*\)')
        wget -q https://download.osgeo.org/gdal/$gdalver/gdal-$GDALVERSION.tar.gz
        tar -xzf gdal-$GDALVERSION.tar.gz
        cd gdal-$gdalver
        if [ -f "CMakeLists.txt" ]; then
            mkdir build
            cd build
            echo "cmake -DCMAKE_INSTALL_PREFIX=$GDALINST/gdal-$GDALVERSION -DPROJ_INCLUDE_DIR=$GDALINST/gdal-$GDALVERSION $GDAL_CMAKE_OPTS -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF .."
            cmake -DCMAKE_INSTALL_PREFIX=$GDALINST/gdal-$GDALVERSION "-DPROJ_INCLUDE_DIR=$GDALINST/gdal-$GDALVERSION" $GDAL_CMAKE_OPTS -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF ..
            cmake --build .
            cmake --build . --target install
        else
            ./configure --prefix=$GDALINST/gdal-$GDALVERSION $GDALOPTS $PROJOPT
            make
            make install
        fi
    fi
fi

# change back to travis build dir
cd $TRAVIS_BUILD_DIR
