#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 FILE"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "File not found: $1"
    exit 1
fi

awk '{print $1}' "$1" | sort | uniq -c | sort -rn | tail -n 5 | awk '{print $2}' | sort | awk -v n=5 -f <(awk 'NR==1{for(i=1;i<=n;i++)printf "%s ",i}1' | tac) | awk '{print NF-1 " " $0}'
