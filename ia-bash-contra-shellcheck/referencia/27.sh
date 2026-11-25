#!/bin/bash
r=0; while IFS= read -r p; do [ -n "$p" ] || continue; [ -e "$p" ] || { echo "FALTA: $p"; r=1; }; done < "$1"; exit $r
