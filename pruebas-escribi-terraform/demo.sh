#!/bin/sh
# demo.sh — la corrida completa del video 218. Todo real, todo desechable.
set -e
cd /app
rm -rf infra estado.json
echo '{"web.conf": "server { listen 80; }", "db.conf": "port = 5432"}' > deseado.json

echo "=== 1 · plan = deseado - actual ==="
echo "  no hay nada creado todavia:"
python tofu_py.py plan deseado.json

echo
echo "=== 2 · apply ==="
python tofu_py.py apply deseado.json
echo "  lo que hay ahora en disco: $(ls infra | tr '\n' ' ')"
echo "  y el estado dice que son mios:"
cat estado.json

echo
echo "=== 3 · plan otra vez, sin tocar nada ==="
python tofu_py.py plan deseado.json
echo "  ^ idempotencia: la resta da cero. No es magia, es que deseado == actual."

echo
echo "=== 4 · cambio el deseado ==="
echo '{"web.conf": "server { listen 443; }", "db.conf": "port = 5432"}' > deseado.json
python tofu_py.py plan deseado.json

echo
echo "############################################################"
echo "### 5 · Y AHORA LO IMPORTANTE:"
echo "###     ALGUIEN CREA UN RECURSO A MANO"
echo "############################################################"
echo "no me toques = de otro equipo" > infra/otro-equipo.conf
echo "  alguien acaba de crear infra/otro-equipo.conf sin pasar por aqui."
echo "  lo que hay ahora: $(ls infra | tr '\n' ' ')"

echo
echo "--- 5a · CON fichero de estado (lo correcto) ---"
python tofu_py.py plan deseado.json
echo "  ^ NO propone borrarlo. No esta en mi estado, asi que no es mio."

echo
echo "--- 5b · SIN fichero de estado (el modo peligroso) ---"
python tofu_py.py plan deseado.json --sin-estado
echo "  ^ PROPONE DESTRUIR EL FICHERO DE OTRO EQUIPO."
echo "    Sin la lista de 'esto lo hice yo', 'lo que sobra' incluye lo que hizo otro."
