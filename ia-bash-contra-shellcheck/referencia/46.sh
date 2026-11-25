#!/bin/bash
echo "$(date +%F) $(du -sb "$1" | cut -f1)" >> "$2"
