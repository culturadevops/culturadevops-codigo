#!/bin/bash

DIR=$1

if [ -z "$DIR" ]; then
    echo "Usage: $0 DIR"
    exit 1
fi

if [ ! -d "$DIR" ]; then
    echo "Error: $DIR is not a valid directory"
    exit 1
fi

find "$DIR" -type f -name "*.log" -size +100k -exec truncate -s 0 {} \;
