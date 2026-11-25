$ ollama --version
ollama version is 0.40.5
$ ollama list
qwen2.5-coder:7b 4.7 GB
qwen2.5-coder:3b 1.9 GB
qwen2.5-coder:1.5b 986 MB
qwen3:1.7b 1.4 GB
$ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NVIDIA GeForce RTX 5070 Ti, 16303 MiB
$ python -c "import os; print(os.cpu_count())"   # núcleos de CPU
24

$ python medir_llm.py qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5
prompt: 'Explica en tres frases qué es un contenedor de Docker.' · máx. 128 tokens · temperatura 0 · GPU
modelo                 frío: carga frío: TTFT TTFT caliente  tokens/s
qwen2.5-coder:1.5b          2.18 s     2.27 s         25 ms     420.3
qwen2.5-coder:3b            2.31 s     2.39 s         23 ms     280.4
qwen2.5-coder:7b            3.09 s     3.18 s         34 ms     153.9

$ python medir_llm.py qwen2.5-coder:1.5b qwen2.5-coder:3b qwen2.5-coder:7b --rondas 5 --cpu
prompt: 'Explica en tres frases qué es un contenedor de Docker.' · máx. 128 tokens · temperatura 0 · SOLO CPU
modelo                 frío: carga frío: TTFT TTFT caliente  tokens/s
qwen2.5-coder:1.5b          1.55 s     1.65 s         42 ms      51.7
qwen2.5-coder:3b            2.32 s     2.49 s         48 ms      28.0
qwen2.5-coder:7b            5.34 s     5.70 s         91 ms      12.5
