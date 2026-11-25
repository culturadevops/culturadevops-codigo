#!/bin/bash
for ((i=0;i<$2;i++)); do [ -e "$1" ] && exit 0; sleep 1; done; [ -e "$1" ]
