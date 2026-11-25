#!/bin/bash
k=$(du -sk "$1" | cut -f1); echo "$k"; [ "$k" -gt "$2" ] && exit 2; exit 0
