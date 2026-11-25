#!/bin/bash
exec 9>"$1"; flock -n 9 || exit 1; echo trabajando >> "$2"
