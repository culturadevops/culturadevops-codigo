#!/bin/bash
find "$1" -maxdepth 1 -type f -name "*.log" -size +100k -exec truncate -s 0 {} +
