#!/bin/bash
find "$1" -type f -name "*.conf" -print0 | while IFS= read -r -d "" f; do if grep -qF -- "$2" "$f"; then cp -- "$f" "$f.orig"; sed -i "s|$2|$3|g" "$f"; fi; done
