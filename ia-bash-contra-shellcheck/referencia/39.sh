#!/bin/bash
for f in "$1"/*.log; do [ -f "$f" ] || continue; m=$(date -r "$f" +%Y-%m); mkdir -p "$1/$m"; mv -- "$f" "$1/$m/"; done
