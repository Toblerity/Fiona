#!/bin/bash
# Example usage:
# GDAL_DIR=$PWD/gdal bash gdal_compile.sh 3.6.0rc2
set -e
pushd .
echo "Building GDAL ($1) from source..."
BUILD_GDAL_DIR=gdal-${1:0:5}
# Download PROJ
if [[ $1 == "git" ]]; then
  git clone https://github.com/OSGeo/GDAL.git ${BUILD_GDAL_DIR}
else
  curl https://download.osgeo.org/gdal/${1:0:5}/gdal-$1.tar.gz > ${BUILD_GDAL_DIR}.tar.gz
  tar zxf ${BUILD_GDAL_DIR}.tar.gz
  rm ${BUILD_GDAL_DIR}.tar.gz
fi
cd ${BUILD_GDAL_DIR}
mkdir build
cd build
# build using cmake
cmake .. \
    -DCMAKE_INSTALL_PREFIX=$GDAL_DIR \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DGDAL_BUILD_OPTIONAL_DRIVERS=OFF \
    -DGDAL_ENABLE_DRIVER_MBTILES=OFF \
    -DOGR_BUILD_OPTIONAL_DRIVERS=OFF \
    -DOGR_ENABLE_DRIVER_CSV=ON \
    -DOGR_ENABLE_DRIVER_DGN=ON \
    -DOGR_ENABLE_DRIVER_DXF=ON \
    -DOGR_ENABLE_DRIVER_FLATGEOBUF=ON \
    -DOGR_ENABLE_DRIVER_GEOJSON=ON \
    -DOGR_ENABLE_DRIVER_GML=ON \
    -DOGR_ENABLE_DRIVER_GMT=ON \
    -DOGR_ENABLE_DRIVER_GPKG=ON \
    -DOGR_ENABLE_DRIVER_GPX=ON \
    -DOGR_ENABLE_DRIVER_OPENFILEGDB=ON \
    -DGDAL_ENABLE_DRIVER_PCIDSK=ON \
    -DOGR_ENABLE_DRIVER_S57=ON \
    -DOGR_ENABLE_DRIVER_SHAPE=ON \
    -DOGR_ENABLE_DRIVER_SQLITE=ON \
    -DOGR_ENABLE_DRIVER_TAB=ON \
    -DOGR_ENABLE_DRIVER_VRT=ON \
    -DBUILD_CSHARP_BINDINGS=OFF \
    -DBUILD_PYTHON_BINDINGS=OFF \
    -DBUILD_JAVA_BINDINGS=OFF
cmake --build . -j$(nproc)
cmake --install .
# cleanup
cd ../..
rm -rf ${BUILD_GDAL_DIR}
popd
