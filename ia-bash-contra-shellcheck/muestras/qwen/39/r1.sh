#!/bin/bash

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

mkdir -p "$DIR/AAAA-MM"

for file in "$DIR"/*.log; do
    if [ -f "$file" ]; then
        mod_date=$(stat -c %y "$file" | awk '{print $1}' | sed 's/\/.*//')
        mod_year=$(echo "$mod_date" | cut -c1-4)
        mod_month=$(echo "$mod_date" | cut -c5-6)
        mod_dir="$DIR/$mod_year-$mod_month"
        mkdir -p "$mod_dir"
        mv "$file" "$mod_dir/"
    fi
done
