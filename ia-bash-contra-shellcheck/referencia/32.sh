#!/bin/bash
for f in "$1"/*.txt; do [ -f "$f" ] && sed -i "s/\r$//" "$f"; done
