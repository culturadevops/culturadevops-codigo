#!/bin/bash
mkdir -p "$2"; for f in "$1"/*.log; do [ -f "$f" ] && cp -- "$f" "$2/"; done
