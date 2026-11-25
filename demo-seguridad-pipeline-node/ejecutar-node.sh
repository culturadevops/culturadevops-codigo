#!/bin/sh
# Corre dentro de node:22-slim: eslint-plugin-security y npm audit.
set -u
cd /demo
for d in app app-arreglada; do (cd $d && npm install --no-audit --no-fund --loglevel=error >/dev/null 2>&1); done
echo "### versiones (node)"
node -v; echo "npm $(npm -v)"; (cd app && npx eslint --version; npm ls eslint-plugin-security --depth=0 | tail -n 2 | head -1)
echo
echo "### 3 · eslint-plugin-security sobre la app vulnerable"
echo "\$ npx eslint ."
(cd app && npx eslint . 2>&1; echo "código de salida: $?")
echo "\$ npx eslint . --max-warnings 0"
(cd app && npx eslint . --max-warnings 0 >/dev/null 2>&1; echo "código de salida: $?")
echo
echo "### 4 · npm audit sobre la app vulnerable (solo lo que se despliega)"
echo "\$ npm audit --omit=dev"
(cd app && npm audit --omit=dev 2>&1; echo "código de salida: $?")
echo
echo "### 5 · el job del pipeline (npm audit --audit-level=high) sobre las dos versiones"
echo "\$ npm audit --omit=dev --audit-level=high   # app"
(cd app && npm audit --omit=dev --audit-level=high >/dev/null 2>&1; echo "código de salida: $?")
echo "\$ npm audit --omit=dev --audit-level=high   # app-arreglada"
(cd app-arreglada && npm audit --omit=dev --audit-level=high 2>&1 | tail -n 2; echo "código de salida: $?")
echo
echo "### 6 · eslint-plugin-security sobre la app arreglada"
(cd app-arreglada && npx eslint . 2>&1; echo "código de salida: $?")
