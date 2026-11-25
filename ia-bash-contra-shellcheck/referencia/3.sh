#!/bin/bash
f=$1; [ -f "$f.5" ] && rm -f -- "$f.5"; for i in 4 3 2 1; do [ -f "$f.$i" ] && mv -- "$f.$i" "$f.$((i+1))"; done; [ -f "$f" ] && mv -- "$f" "$f.1"; : > "$f"
