#!/usr/bin/env bash
# Demo del vídeo 471 «Proyecto de IA 1 (Python)» — se EJECUTA y su salida va a SALIDA.md.
# Una app Flask que usa psycopg2 (sin Dockerfile) y dockerfile_ia.py: un LLM local en Ollama escribe el Dockerfile, docker build
# lo prueba, los errores vuelven al modelo, y al final se comprueba GET /salud con el contenedor corriendo.
# Trabaja sobre una copia en un directorio temporal; borra las imágenes ia-demo:* al terminar.
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
T=$(mktemp -d)
cp -r "$AQUI/app" "$T/app"
echo '$ ollama --version'; ollama --version 2>&1 | tail -1
echo '$ ollama list | grep qwen2.5-coder'; ollama list | grep qwen2.5-coder | awk '{print $1, $3, $4}'
echo '$ nvidia-smi --query-gpu=name --format=csv,noheader'; nvidia-smi --query-gpu=name --format=csv,noheader
echo
echo '$ ls app && cat app/requirements.txt'; ls "$T/app"; cat "$T/app/requirements.txt"
echo
for caso in "qwen2.5-coder:7b cola" "qwen2.5-coder:7b relevantes" "qwen2.5-coder:1.5b relevantes"; do
  set -- $caso
  echo "\$ python dockerfile_ia.py app --modelo $1 --errores $2"
  rm -f "$T/app/Dockerfile"
  (cd "$T" && PYTHONUTF8=1 python "$AQUI/dockerfile_ia.py" app --modelo "$1" --errores "$2"; echo "(código de salida: $?)")
  echo
done
echo '$ # la versión del modelo, revisada por una persona (Dockerfile.revisado)'
cp "$AQUI/Dockerfile.revisado" "$T/app/Dockerfile"
echo '$ docker build -t ia-demo:revisado app && docker run -d -p 18080:8080 ia-demo:revisado && curl /salud'
(cd "$T/app" && docker build -q -t ia-demo:revisado . >/dev/null 2>&1) && echo "  build: ok"
docker rm -f ia-demo >/dev/null 2>&1
docker run -d --name ia-demo -p 18080:8080 ia-demo:revisado >/dev/null
for i in $(seq 1 20); do r=$(curl -s -m 2 http://127.0.0.1:18080/salud) && [ -n "$r" ] && break; sleep 1; done
echo "  GET /salud -> $r"
echo "  usuario dentro del contenedor: $(docker exec ia-demo whoami)"
echo "  ¿hay gcc en la imagen final?: $(docker exec ia-demo sh -c 'command -v gcc || echo no')"
echo "  imagen: $(( $(docker image inspect -f '{{.Size}}' ia-demo:revisado) / 1000000 )) MB"
echo
docker rm -f ia-demo >/dev/null 2>&1
docker images --format '{{.Repository}}:{{.Tag}}' | grep '^ia-demo:' | xargs -r docker rmi -f >/dev/null 2>&1
cd / && rm -rf "$T"
