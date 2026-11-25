#!/usr/bin/env bash
# demo.sh — la medición del vídeo 229 «Loki, ¿la alternativa a Elasticsearch este 2026?».
#
# ⛔ LA REGLA: el MISMO corpus (registros.jsonl, 200.000 líneas, semilla fija) en los dos.
# Y se miden las DOS clases de búsqueda, o el vídeo sería propaganda:
#   · por ETIQUETA   (servicio=pagos, nivel=ERROR)  ← donde Loki debería ir bien
#   · por CONTENIDO  (una frase que sale 10 veces)  ← donde Elasticsearch debería ir bien
set -u
D=$(cd "$(dirname "$0")" && pwd -W)
R=logred

limpiar() { docker rm -f loki elastic >/dev/null 2>&1; docker network rm $R >/dev/null 2>&1; }
limpiar; docker network create $R >/dev/null

echo "== 0 · EL CORPUS, el mismo para los dos =="
echo -n "   lineas: "; wc -l < "$D/registros.jsonl" | tr -d ' '
echo -n "   tamano: "; du -h "$D/registros.jsonl" | cut -f1
echo    "   la aguja («pago rechazado por el banco emisor») sale 10 veces"

echo
echo "== 1 · LEVANTO LOS DOS =="
docker run -d --name loki --network $R \
  -v "$D/loki-config.yaml:/etc/loki/local-config.yaml" \
  grafana/loki:3.2.0 >/dev/null
sleep 10
docker logs loki 2>&1 | grep -iE 'error|failed|panic' | head -3
docker run -d --name elastic --network $R \
  -e discovery.type=single-node -e xpack.security.enabled=false \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  docker.elastic.co/elasticsearch/elasticsearch:8.15.0 >/dev/null
echo -n "   esperando a Elasticsearch"
for i in $(seq 1 90); do
  docker exec elastic curl -s localhost:9200/_cluster/health >/dev/null 2>&1 && break
  echo -n "."; sleep 3
done; echo
docker exec elastic curl -s localhost:9200 | grep -E '"number"|"tagline"' | tr -d ' '
docker exec loki wget -qO- http://localhost:3100/ready 2>/dev/null || echo "loki listo"

echo
echo "== 2 · MEMORIA EN REPOSO, antes de meter un solo registro =="
docker stats --no-stream --format '   {{.Name}}: {{.MemUsage}}' loki elastic

echo
echo "== 3 · INGERIR LAS MISMAS 200.000 LINEAS =="
docker run --rm --network $R -v "$D:/w" -w /w python:3.12-slim sh -c '
pip -q install requests >/dev/null 2>&1; python /w/ingerir.py' 2>&1 | sed 's/^/   /'

echo
echo "== 4 · LO QUE OCUPA EN DISCO =="
# ⚠️ Hay que esperar a que Loki vuelque sus trozos: los tiene en memoria hasta que caducan.
#    Sin esta espera el disco sale en kilobytes y la medicion es mentira.
echo "   (esperando a que Loki vuelque sus trozos...)"; sleep 25
docker exec elastic curl -s "localhost:9200/registros/_forcemerge?max_num_segments=1" >/dev/null 2>&1
sleep 8
echo -n "   Elasticsearch (indice registros): "
docker exec elastic curl -s "localhost:9200/_cat/indices/registros?h=store.size,docs.count" | tr -s ' '
echo -n "   Loki (todo su directorio de datos): "
docker exec loki du -sh /loki 2>/dev/null | cut -f1
echo -n "   Loki, solo los trozos (los datos de verdad): "
docker exec loki du -sh /loki/chunks 2>/dev/null | cut -f1

echo
echo "== 5 · MEMORIA DESPUES DE INGERIR =="
docker stats --no-stream --format '   {{.Name}}: {{.MemUsage}}' loki elastic

echo
echo "== 6 · LAS DOS BUSQUEDAS =="
docker run --rm --network $R -v "$D:/w" -w /w python:3.12-slim sh -c '
pip -q install requests >/dev/null 2>&1; python /w/buscar.py' 2>&1 | sed 's/^/   /'

limpiar
echo
echo "== limpio =="
