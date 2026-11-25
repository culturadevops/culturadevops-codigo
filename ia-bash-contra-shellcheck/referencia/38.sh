#!/bin/bash
n=$1; log=$2; shift 2; if ! pgrep -x "$n" >/dev/null; then "$@" & echo reiniciado >> "$log"; fi
