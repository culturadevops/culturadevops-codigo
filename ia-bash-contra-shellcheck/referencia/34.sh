#!/bin/bash
u=$(df -P "$1" | awk "NR==2{gsub(/%/,\"\",\$5); print \$5}"); if [ "$u" -gt "$2" ]; then echo ALERTA; else echo OK; fi
