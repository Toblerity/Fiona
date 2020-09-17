#!/bin/bash

# Install filegdb if not already installed
if [ ! -d "$FILEGDB" ]; then
  mkdir -p $FILEGDB
  cd $FILEGDB
  wget -q https://github.com/Esri/file-geodatabase-api/raw/master/FileGDB_API_1.5.1/FileGDB_API_1_5_1-64gcc51.tar.gz
  tar -xzf FileGDB_API_1_5_1-64gcc51.tar.gz --strip=1 FileGDB_API-64gcc51
  rm FileGDB_API_1_5_1-64gcc51.tar.gz
  rm -rf samples
  rm -rf doc
fi

export LD_LIBRARY_PATH=$FILEGDB/lib:$LD_LIBRARY_PATH

# change back to travis build dir
cd $TRAVIS_BUILD_DIR

