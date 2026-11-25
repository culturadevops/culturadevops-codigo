#!/bin/bash
b=$(basename -- "$1"); t="$2/$b"; [ -e "$t" ] && t="$2/$(date +%Y%m%d-%H%M%S)_$b"; cp -- "$1" "$t"
