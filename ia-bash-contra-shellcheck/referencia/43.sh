#!/bin/bash
cd "$1" || exit 1; find . -type f -name "*.txt" -print0 | while IFS= read -r -d "" f; do mkdir -p -- "$2/$(dirname -- "$f")"; cp -- "$f" "$2/$f"; done
