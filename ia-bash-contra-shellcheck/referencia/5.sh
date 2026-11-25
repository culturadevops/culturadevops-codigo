#!/bin/bash
for f in "$1"/*.txt; do [ -f "$f" ] && printf "%s: %s\n" "$(basename -- "$f")" "$(wc -l < "$f")"; done
