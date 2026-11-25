#!/bin/bash
for f in "$1"/*.tar.gz; do [ -f "$f" ] || continue; d=${f%.tar.gz}; mkdir -p -- "$d"; tar -xzf "$f" -C "$d"; done
