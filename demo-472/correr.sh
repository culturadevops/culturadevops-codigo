#!/usr/bin/env bash
# Demo del vídeo 472 «Proyecto de IA 2 (Python)» — se EJECUTA y su salida va a SALIDA.md.
# medir_llm.py contra tres modelos locales de Ollama, con GPU y forzando solo CPU (num_gpu=0).
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
echo '$ ollama --version'; ollama --version 2>&1 | tail -1
echo '$ ollama list'; ollama list | awk 'NR>1 && $1 !~ /embed/ {print $1, $3, $4}'
echo '$ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader'; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo '$ python -c "import os; print(os.cpu_count())"   # núcleos de CPU'; python -c "import os; print(os.cpu_count())"
echo
echo '$ python medir_llm.py qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5'
PYTHONUTF8=1 python "$AQUI/medir_llm.py" qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5
echo
echo '$ python medir_llm.py qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5 --cpu'
PYTHONUTF8=1 python "$AQUI/medir_llm.py" qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5 --cpu
