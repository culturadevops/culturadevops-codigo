#!/bin/bash

DIR=$1

if [ -z "$DIR" ]; then
    echo "Usage: $0 DIR"
    exit 1
fi

if [ ! -d "$DIR" ]; then
    echo "$DIR is not a directory"
    exit 1
fi

find "$DIR" -maxdepth 1 -type f -name "*.log" -exec awk '
    FNR == 1 {print "== " FILENAME " ==\n" $0}
    FNR == 2 {print $0}
' {} \;
