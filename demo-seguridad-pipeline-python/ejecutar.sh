#!/bin/sh
# Corre dentro de python:3.13-slim. Instala las herramientas con versión fija y escanea las dos versiones de la app.
set -u
pip install -q --root-user-action=ignore bandit==1.9.4 pip-audit==2.10.1 semgrep==1.182.1 >/dev/null 2>&1
echo "### versiones"
bandit --version | head -1; pip-audit --version; semgrep --version
cd /demo
echo
echo "### 1 · bandit sobre la app vulnerable (todas las severidades)"
echo "\$ bandit -r app/"
bandit -r app/ -f txt 2>&1 | sed -n '/Test results/,/Code scanned/p'
echo
echo "### 2 · pip-audit sobre requirements.txt"
echo "\$ pip-audit -r app/requirements.txt"
pip-audit -r app/requirements.txt --progress-spinner off 2>&1
echo
echo "### 3 · semgrep con las reglas de Python y Flask"
echo "\$ semgrep --config p/python --config p/flask app/"
semgrep --config p/python --config p/flask --metrics=off --quiet app/ 2>&1
echo
echo "### 3b · semgrep con las reglas de secretos (la clave de Stripe)"
echo "\$ semgrep --config p/secrets app/"
semgrep --config p/secrets --metrics=off --quiet app/ 2>&1
echo
echo "### 3c · bandit SOLO con severidad alta (-lll): ¿cuántos de los 4 fallos ve?"
echo "\$ bandit -r app/ -lll"
bandit -q -r app/ -lll -f csv 2>/dev/null | cut -d, -f3,4,6,7
echo
echo "### 4 · el job del pipeline sobre la app vulnerable"
echo "\$ ./ci-seguridad.sh app"
sh ci-seguridad.sh app; echo "código de salida: $?"
echo
echo "### 5 · el mismo job sobre la app arreglada"
echo "\$ ./ci-seguridad.sh app-arreglada"
sh ci-seguridad.sh app-arreglada; echo "código de salida: $?"
echo
echo "### 6 · semgrep sobre la app arreglada"
semgrep --config p/python --config p/flask --metrics=off --quiet app-arreglada/ 2>&1; echo "código de salida: $?"
echo
echo "### 7 · un nosec con texto detrás de los códigos"
printf 'import subprocess
subprocess.check_output(["ping", "-c", "1", "127.0.0.1"])  # nosec B603 B607 -- argumentos fijos, IP validada
' > /tmp/nosec.py
cat /tmp/nosec.py
echo "\$ bandit /tmp/nosec.py"
bandit -q /tmp/nosec.py 2>&1 | grep WARNING
