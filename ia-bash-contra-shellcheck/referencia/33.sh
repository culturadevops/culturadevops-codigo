#!/bin/bash
mkdir -p "$2"; find "$1" -type f -name "*.log" -print0 | sort -z | xargs -0 cat > "$2/todo.log"
