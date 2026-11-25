#!/bin/bash
for f in $(find $1 -name "*.log"); do cat $f; done | grep -c ERROR
