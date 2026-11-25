#!/bin/bash

FILE=$1

if [ -f "$FILE" ]; then
    count=5
    while [ $count -gt 1 ]; do
        prev_file="$FILE.$((count-1))"
        if [ -f "$prev_file" ]; then
            mv "$prev_file" "$FILE.$count"
        fi
        count=$((count-1))
    done
    mv "$FILE" "$FILE.1"
    touch "$FILE"
else
    touch "$FILE"
fi
