#!/bin/bash
grep -v "^#" "$1" | grep "^$2=" | head -1 | cut -d= -f2-
