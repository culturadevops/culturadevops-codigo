#!/usr/bin/env bash
# demo.sh — la corrida entera del vídeo 221, con Grafana OFICIAL.
#
# Tres contenedores en la misma red de Docker:
#   app          servicio de Python que expone /metrics
#   prometeillo  nuestro Prometheus de juguete, que VA A BUSCAR esas métricas
#   grafana      la imagen oficial grafana/grafana, sin parches ni adaptadores
#
# La prueba de que funciona no es una captura: es que Grafana conteste con datos
# a través de su propia API de consulta, que es la que usa un panel para pintar.
set -u
D=$(cd "$(dirname "$0")" && pwd -W)
R=promred

limpiar() { docker rm -f app prometeillo grafana >/dev/null 2>&1; docker network rm $R >/dev/null 2>&1; }
limpiar
docker network create $R >/dev/null

echo "== 1 · levanto el servicio que va a ser medido =="
docker run -d --name app --network $R -v "$D:/w" -w /w python:3.12-alpine \
  python app.py >/dev/null
sleep 3
echo "-- el formato de exposición es TEXTO. Esto es lo que hay en /metrics:"
docker exec app python -c "
import urllib.request
print(urllib.request.urlopen('http://localhost:9101/metrics').read().decode()[:520])"

echo
echo "== 2 · levanto prometeillo, que va a buscarlas cada 2 segundos =="
docker run -d --name prometeillo --network $R -v "$D:/w" -w /w python:3.12-alpine \
  python prometeillo.py >/dev/null
sleep 12

echo "== 3 · Grafana OFICIAL, imagen sin tocar =="
docker run -d --name grafana --network $R -p 3000:3000 \
  -e GF_AUTH_ANONYMOUS_ENABLED=true -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:latest >/dev/null
echo -n "   esperando a Grafana"
for i in $(seq 1 60); do
  docker exec grafana wget -qO- http://localhost:3000/api/health 2>/dev/null | grep -q ok && break
  echo -n "."; sleep 2
done
echo
docker exec grafana wget -qO- http://localhost:3000/api/health

echo
echo "== 4 · le digo a Grafana que esto es un Prometheus =="
docker exec grafana wget -qO- --header='Content-Type: application/json' \
  --post-data='{"name":"prometeillo","type":"prometheus","access":"proxy","url":"http://prometeillo:9090","isDefault":true}' \
  http://admin:admin@localhost:3000/api/datasources

echo
echo "== 5 · el botón de «Guardar y probar» de Grafana, por su API =="
DSUID=$(docker exec grafana wget -qO- http://admin:admin@localhost:3000/api/datasources \
      | tr ',' '\n' | grep -o '"uid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "   uid=$DSUID"
docker exec grafana wget -qO- "http://admin:admin@localhost:3000/api/datasources/uid/$DSUID/health"

echo
echo
echo "== 6 · LA PRUEBA DE VERDAD: un panel pidiendo datos a través de Grafana =="
echo "   (esto es exactamente lo que manda un panel de serie temporal al cargarse)"
AHORA=$(date +%s)
DESDE=$(( (AHORA - 120) * 1000 )); HASTA=$(( AHORA * 1000 ))
docker exec grafana sh -c "wget -qO- --header='Content-Type: application/json' \
  --post-data='{\"from\":\"$DESDE\",\"to\":\"$HASTA\",\"queries\":[{\"refId\":\"A\",\"datasource\":{\"type\":\"prometheus\",\"uid\":\"$DSUID\"},\"expr\":\"peticiones_total\",\"range\":true,\"intervalMs\":5000,\"maxDataPoints\":50}]}' \
  http://admin:admin@localhost:3000/api/ds/query" | python -c "
import json,sys
r=json.load(sys.stdin)
fr=r['results']['A']['frames']
print(f'   Grafana devolvio {len(fr)} series al panel')
for f in fr[:4]:
    n=f['schema']['fields'][1]['labels']
    vals=f['data']['values'][1]
    print(f\"     {n.get('ruta','?'):12} codigo={n.get('codigo','?')}  {len(vals)} puntos  \"
          f'ultimo={vals[-1]}')
print()
print('   ^ Grafana pinto esto sin saber que detras hay 200 lineas de Python.')
"

echo
echo "== 7 · LA CARDINALIDAD: qué pasa si etiquetas por usuario =="
echo -n "   series ahora mismo, sin etiqueta de usuario: "
docker exec prometeillo python -c "
import urllib.request,json
d=json.load(urllib.request.urlopen('http://localhost:9090/api/v1/query?query=peticiones_total'))
print(len(d['data']['result']))"
docker rm -f app >/dev/null
docker run -d --name app --network $R -v "$D:/w" -w /w -e MODO_CARDINALIDAD=1 \
  python:3.12-alpine python app.py >/dev/null
echo "   ...reinicio la app con una etiqueta usuario=\"uN\" y espero 20 segundos..."
sleep 20
echo -n "   series con la etiqueta de usuario:           "
docker exec prometeillo python -c "
import urllib.request,json
d=json.load(urllib.request.urlopen('http://localhost:9090/api/v1/query?query=peticiones_total'))
print(len(d['data']['result']))"
echo "   ^ y esto sube para siempre, con cada usuario nuevo. Ese es el coste que se paga."

echo
echo "== 8 · la métrica que NADIE expone y siempre está: up =="
docker exec prometeillo python -c "
import urllib.request,json
d=json.load(urllib.request.urlopen('http://localhost:9090/api/v1/query?query=up'))
for s in d['data']['result']:
    print('   up', s['metric'], '=', s['value'][1])"
echo "   ^ la escribe el que recoge, no el medido. Por eso puedes alertar de algo muerto."

echo
echo "== 9 · POR QUE UN PROCESO CORTO NO APARECE NUNCA =="
echo "   levanto un trabajo que vive 3 segundos y expone su metrica todo ese rato,"
echo "   con el scrape cada 2 s. Y luego pregunto si quedo algun punto suyo."
docker run -d --name trabajito --network $R python:3.12-alpine sh -c "
python - <<'PY'
import threading,time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a): pass
    def do_GET(self):
        c=b'trabajito_hecho 1\n'
        self.send_response(200); self.send_header('Content-Length',str(len(c))); self.end_headers()
        self.wfile.write(c)
s=ThreadingHTTPServer(('0.0.0.0',9101),H)
threading.Thread(target=s.serve_forever,daemon=True).start()
time.sleep(3)
PY
" >/dev/null
sleep 6
echo -n "   puntos guardados de trabajito_hecho: "
docker exec prometeillo python -c "
import urllib.request,json
d=json.load(urllib.request.urlopen('http://localhost:9090/api/v1/query?query=trabajito_hecho'))
print(len(d['data']['result']))"
echo "   ^ CERO. Existio 3 segundos, expuso su metrica los 3 segundos, y no queda rastro."
echo "     Nadie fue a buscarla a ESE host: el que recoge solo conoce la lista de objetivos"
echo "     que le diste. Por eso los trabajos cortos van por otro camino (un pushgateway),"
echo "     y por eso este modelo se llama de tiron y no de empuje."
docker rm -f trabajito >/dev/null 2>&1
