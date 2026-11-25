#!/bin/bash
find "$1" -type f -printf "%s\t%p\n" | sort -rn | head -3 | cut -f2-
