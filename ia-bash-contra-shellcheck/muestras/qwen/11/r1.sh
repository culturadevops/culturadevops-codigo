#!/bin/bash

DIR=$1

if [ -z "$DIR" ]; then
    echo "Usage: $0 DIR"
    exit 1
fi

if [ ! -d "$DIR" ]; then
    echo "Error: $DIR is not a directory"
    exit 1
fi

cd "$DIR" || exit

for file in *; do
    if [ -f "$file" ]; do
        ext="${file##*.}"
        mkdir -p "$ext/"
        mv "$file" "$ext/"
    fi
done
