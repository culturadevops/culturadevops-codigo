#!/bin/bash
for f in "$1"/*.*; do [ -f "$f" ] || continue; e=${f##*.}; e=${e,,}; mkdir -p "$1/$e"; mv -- "$f" "$1/$e/"; done
