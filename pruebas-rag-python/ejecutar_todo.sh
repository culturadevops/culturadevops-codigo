#!/usr/bin/env bash
# Corrida completa del vídeo 797. Necesita Docker y Ollama en el host con nomic-embed-text, bge-m3 y qwen2.5:7b.
# Todo con --rm; la red y Postgres se quitan al final. Uso: bash ejecutar_todo.sh > corrida.txt 2>&1
set -u
cd "$(dirname "$0")"
docker build -q -t cd797-rag:1 . >/dev/null
docker network create cd797-net >/dev/null 2>&1 || true
docker run --rm -d --name cd797-pg --network cd797-net --cpus 1 -e POSTGRES_PASSWORD=demo pgvector/pgvector:pg17 >/dev/null
until docker exec cd797-pg pg_isready -U postgres -q 2>/dev/null; do sleep 1; done
sleep 2

rag() {  # rag EMB [UMBRAL] accion args...
  local emb="$1" umbral="$2"; shift 2
  echo "\$ EMB=$emb${umbral:+ UMBRAL=$umbral} python rag.py $1 ${2:+\"$2\"}"
  docker run --rm --network cd797-net --cpus 1 --add-host host.docker.internal:host-gateway \
    -e EMB="$emb" -e UMBRAL="${umbral:-0}" cd797-rag:1 "$@"
  echo
}

echo "=== versiones"
docker run --rm --entrypoint python cd797-rag:1 -c "import sys,psycopg;print('python',sys.version.split()[0],'· psycopg',psycopg.__version__)"
docker exec cd797-pg psql -U postgres -tAc "CREATE EXTENSION IF NOT EXISTS vector; SELECT 'postgres ' || current_setting('server_version') || ' · pgvector ' || extversion FROM pg_extension WHERE extname='vector'"
curl -s http://localhost:11434/api/version; echo
echo

echo "=== A · nomic-embed-text (768), con los prefijos search_document/search_query"
rag nomic-embed-text "" indexar
for q in "¿Puedo desplegar un viernes?" "¿Qué pasa si la guardia no contesta una alerta?" \
         "¿Cuánto tiempo se guardan las copias de seguridad?" "¿Cuánto tiempo se guardan los respaldos?"; do
  rag nomic-embed-text "" buscar "$q"
done
rag nomic-embed-text "" preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"

echo "=== B · bge-m3 (1024, multilingüe)"
rag bge-m3 "" indexar
for q in "¿Puedo desplegar un viernes?" "¿Qué pasa si la guardia no contesta una alerta?" \
         "¿Cuánto tiempo se guardan las copias de seguridad?" "¿Cuál es el presupuesto de la nube para 2027?"; do
  rag bge-m3 "" buscar "$q"
done
rag bge-m3 "" preguntar "¿Puedo desplegar un viernes?"
rag bge-m3 "" preguntar "¿Qué pasa si la guardia no contesta una alerta?"
rag bge-m3 "" preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"

echo "=== C · la pregunta sin respuesta"
rag bge-m3 "" preguntar "¿Cuál es el presupuesto de la nube para 2027?"
rag bge-m3 0.5 preguntar "¿Cuál es el presupuesto de la nube para 2027?"
rag bge-m3 0.5 preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"

echo "=== D · ¿usa el índice HNSW?"
echo "\$ psql -c \"EXPLAIN SELECT ... ORDER BY emb <=> ... LIMIT 3\""
docker exec cd797-pg psql -U postgres -c "\\d trozos" | grep -i hnsw
docker exec cd797-pg psql -U postgres -c "EXPLAIN (COSTS OFF) SELECT doc, n FROM trozos ORDER BY emb <=> (SELECT emb FROM trozos WHERE id=1) LIMIT 3"
docker exec cd797-pg psql -U postgres -c "SET enable_seqscan = off" -c "EXPLAIN (COSTS OFF) SELECT doc, n FROM trozos ORDER BY emb <=> (SELECT emb FROM trozos WHERE id=1) LIMIT 3"

echo "=== E · el tamaño"
docker exec cd797-pg psql -U postgres -tAc "SELECT count(*) || ' trozos · tabla ' || pg_size_pretty(pg_total_relation_size('trozos')) FROM trozos"
wc -l rag.py
docker images cd797-rag:1 --format "imagen {{.Size}}"

docker stop cd797-pg >/dev/null
docker network rm cd797-net >/dev/null
