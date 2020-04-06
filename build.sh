#!/bin/bash

# Cleanup
rm -rf ./build
mkdir -p ./build

# Backup
cp -r ./src ./build/Back

# Prepare
cp -r ./src ./build/Marz

# Compress
cd ./build
zip -r Marz.zip Marz -x "Marz/__pycache__/*" -x "Marz/notes.ipynb" -x "Marz/.env"

# Update Version in source
cd ..
sed -r -E -i 's/MARZ_VERSION([[:space:]]*)=([[:space:]]*)"([0-9]*).([0-9]*).([0-9]*)-(.*)"/echo "MARZ_VERSION\1=\2\\"\3.\4.$((\5+1))-\6\\""/ge' ./src/marz_ui.py

