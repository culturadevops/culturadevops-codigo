#!/bin/bash
for i in 1 2 3; do "$@"; rc=$?; [ $rc -eq 0 ] && exit 0; [ $i -lt 3 ] && sleep 1; done; exit $rc
