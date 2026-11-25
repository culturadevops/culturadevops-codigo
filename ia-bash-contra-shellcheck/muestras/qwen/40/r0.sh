#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 DIR"
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "Error: $DIR is not a valid directory"
    exit 1
fi

find "$DIR" -maxdepth 1 -type f -name "*.txt" -exec sed -i 's/[ \t]*$//' {} \;
