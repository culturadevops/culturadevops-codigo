#!/bin/bash
awk "{print \$1}" "$1" | sort | uniq -c | sort -rn | head -5 | awk "{print \$1, \$2}"
