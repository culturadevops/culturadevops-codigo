#!/bin/bash
log=$1; shift; "$@" 2>&1 | while IFS= read -r l; do printf "[%s] %s\n" "$(date "+%F %T")" "$l"; done >> "$log"
