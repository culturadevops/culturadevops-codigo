#!/bin/bash

DIR=$1
FILE=$2

DATE=$(date +%Y-%m-%d)
SIZE=$(du -sb "$DIR" | awk '{print $1}')

echo "$DATE $SIZE" >> "$FILE"
