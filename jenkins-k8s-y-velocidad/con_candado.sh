#!/usr/bin/env bash
# Ejecuta un comando con el candado de la fábrica (_logs/banco.lock): nadie mide mientras otro mide o carga la máquina.
L=<proyecto>/_logs/banco.lock
until mkdir "$L" 2>/dev/null; do echo "candado ocupado: $(cat $L/* 2>/dev/null | head -1)"; sleep 30; done
echo "jk-b (877-878) $(date -u +%FT%TZ)" > "$L/dueño-jk-b.txt"
trap 'rm -f "$L/dueño-jk-b.txt"; rmdir "$L"' EXIT
"$@"
