#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 FILE"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "File not found: $1"
    exit 1
fi

awk -F',' '{print $2}' "$1"
