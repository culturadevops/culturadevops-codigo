#!/bin/bash
n=$(find "$1" -type f \( -name "*.tmp" -o -name "*.bak" \) -print -delete | wc -l); echo "$n"
