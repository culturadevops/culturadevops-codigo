#!/bin/bash
tar -czf "$2/respaldo-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$1" .; ls -1t "$2"/*.tar.gz | tail -n +4 | while IFS= read -r f; do rm -f -- "$f"; done
