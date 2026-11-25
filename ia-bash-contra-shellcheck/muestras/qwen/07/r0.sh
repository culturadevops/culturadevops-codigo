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

find "$DIR" -maxdepth 1 -type f -name "*.log" ! -name "*.log.gz" -exec gzip {} \;
