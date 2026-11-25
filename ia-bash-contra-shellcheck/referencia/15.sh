#!/bin/bash
for f in "$1"/*.txt; do [ -f "$f" ] || continue; d=$(date -r "$f" +%Y-%m-%d); mv -- "$f" "$(dirname -- "$f")/${d}_$(basename -- "$f")"; done
