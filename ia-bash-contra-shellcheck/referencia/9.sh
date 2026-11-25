#!/bin/bash
cd "$1" || exit 1; find . -maxdepth 1 -type f ! -name SHA256SUMS -printf "%P\0" | xargs -0 sha256sum > SHA256SUMS
