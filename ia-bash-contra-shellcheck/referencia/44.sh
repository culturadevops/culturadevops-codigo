#!/bin/bash
for f in "$1"/*.log; do [ -f "$f" ] || continue; echo "== $(basename -- "$f") =="; head -n 2 -- "$f"; done
