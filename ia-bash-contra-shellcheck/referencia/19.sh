#!/bin/bash
find "$1" -type f -exec sha256sum {} + | sort | uniq -w64 --all-repeated=separate | cut -c67-
