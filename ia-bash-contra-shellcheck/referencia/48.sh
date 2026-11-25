#!/bin/bash
find "$1" -type f -name "*.csv" -print0 | while IFS= read -r -d "" f; do echo "$(basename -- "$f"): $(( $(wc -l < "$f") - 1 )) filas"; done
