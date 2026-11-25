#!/usr/bin/env bash
# corre las partes 5, 6 y 7 seguidas (banco del agente B)
cd "$(dirname "$0")/.."
for n in 5 6 7; do bash parte-$n/correr-parte-$n.sh > /dev/null 2>&1; echo "parte $n terminada $(date +%T)"; done
