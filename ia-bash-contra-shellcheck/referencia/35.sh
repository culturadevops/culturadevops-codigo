#!/bin/bash
while IFS= read -r u; do [ -n "$u" ] && echo "useradd -m $u"; done < "$1"
