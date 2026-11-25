#!/bin/bash
find "$1" -type f -name "*.*" -printf "%f\n" | sed "s/.*\.//" | sort | uniq -c | sort -rn | awk "{print \$2, \$1}"
