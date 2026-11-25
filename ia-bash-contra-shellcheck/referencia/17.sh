#!/bin/bash
cd "$1" || exit 1; find . -type f -print0 | while IFS= read -r -d "" f; do t="$2/$f"; if [ ! -e "$t" ] || [ "$f" -nt "$t" ]; then mkdir -p -- "$(dirname -- "$t")"; cp -p -- "$f" "$t"; fi; done
