#!/bin/bash
find "$1" -type f -name "*.log" -exec cat {} + | grep -c ERROR
