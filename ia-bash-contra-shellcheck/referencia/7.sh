#!/bin/bash
for f in "$1"/*.log; do [ -f "$f" ] && gzip -- "$f"; done
