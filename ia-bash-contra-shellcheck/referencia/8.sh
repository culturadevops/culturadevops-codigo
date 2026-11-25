#!/bin/bash
for f in "$1"/*.*; do [ -f "$f" ] || continue; b=${f%.*}; e=${f##*.}; l=$(printf "%s" "$e" | tr "[:upper:]" "[:lower:]"); [ "$e" != "$l" ] && mv -- "$f" "$b.$l"; done; true
