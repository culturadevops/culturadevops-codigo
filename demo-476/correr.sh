#!/usr/bin/env bash
# Demo del vídeo 476 «Agentes de IA en producción (medido)» — se EJECUTA y su salida va a SALIDA.md.
# Un agente de soporte mínimo (agente.py) con una herramienta de LECTURA y una de ESCRITURA, sobre Ollama local, y cuatro
# experimentos (experimentos.py): tareas de 1, 3 y 5 llamadas · traza JSON · inyección de instrucciones sin y con guardas ·
# ruteo de modelos. La tienda es de mentira: ningún dinero real.
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI"
export PYTHONUTF8=1
echo '$ ollama --version'; ollama --version 2>&1 | tail -1
echo '$ ollama list | grep "qwen2.5:"'; ollama list | grep "qwen2.5:" | awk '{print $1, $3, $4}'
echo
echo '$ python experimentos.py traza qwen2.5:1.5b'
python experimentos.py traza qwen2.5:1.5b
echo
echo '$ python experimentos.py traza qwen2.5:7b'
python experimentos.py traza qwen2.5:7b
echo
echo '$ python experimentos.py pasos qwen2.5:1.5b qwen2.5:7b'
python experimentos.py pasos qwen2.5:1.5b qwen2.5:7b
echo
echo '$ python experimentos.py pasos-v2 qwen2.5:1.5b qwen2.5:7b   # + buscar_pedidos(lista)'
python experimentos.py pasos-v2 qwen2.5:1.5b qwen2.5:7b
echo
echo '$ python experimentos.py pasos-v3 qwen2.5:1.5b qwen2.5:7b   # + sumar(números) y la instrucción de usarla'
python experimentos.py pasos-v3 qwen2.5:1.5b qwen2.5:7b
echo '$ # las mismas tres pruebas del 7B, otra vez: ¿salen igual?'
for v in pasos pasos-v2 pasos-v3; do python experimentos.py $v qwen2.5:7b | tail -1 | sed "s/^/  $v: /"; done
echo
echo '$ python experimentos.py inyeccion qwen2.5:7b'
python experimentos.py inyeccion qwen2.5:7b
echo
echo '$ python experimentos.py ruteo qwen2.5:1.5b qwen2.5:7b'
python experimentos.py ruteo qwen2.5:1.5b qwen2.5:7b
