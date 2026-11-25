# -*- coding: utf-8 -*-
"""Genera los archivos de la demo «seguridad en el pipeline para Node.js» (cultura-devops). python generar.py"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))


def W(p, t):
    p = os.path.join(AQUI, p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


VULN = """// Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops). No la despliegues.
const express = require('express');
const mysql = require('mysql2');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const _ = require('lodash');

const app = express();
const db = mysql.createConnection({ host: 'db', user: 'tienda', database: 'tienda' });
// Fallo 4: una clave pegada en el código
const STRIPE_API_KEY = 'CLAVE_STRIPE_FALSA_DE_EJEMPLO';

app.get('/producto', (req, res) => {
  // Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
  db.query(`SELECT id, nombre, precio FROM productos WHERE nombre = '${req.query.nombre}'`, (err, filas) => res.json(filas));
});

app.get('/ping', (req, res) => {
  // Fallo 2: inyección de comandos
  exec('ping -c 1 ' + req.query.host, (err, salida) => res.send(salida));
});

app.get('/factura', (req, res) => {
  // Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
  res.send(fs.readFileSync(path.join('/srv/facturas', req.query.archivo), 'utf8'));
});

app.post('/preferencias', express.json(), (req, res) => {
  // Extra: mezcla un objeto que manda el usuario (con lodash vulnerable, prototype pollution)
  res.json(_.merge({}, req.body));
});

app.listen(3000);
"""

ARREGLADA = """// La misma tienda, con los fallos arreglados (demo de cultura-devops).
const express = require('express');
const mysql = require('mysql2');
const { execFile } = require('child_process');
const fs = require('fs');
const net = require('net');
const path = require('path');

const app = express();
const db = mysql.createConnection({ host: 'db', user: 'tienda', database: 'tienda' });
// Arreglo 4: la clave viene del entorno (en el pipeline, de un gestor de secretos)
const STRIPE_API_KEY = process.env.STRIPE_API_KEY;
const FACTURAS = path.resolve('/srv/facturas');

app.get('/producto', (req, res) => {
  // Arreglo 1: consulta con parámetros
  db.execute('SELECT id, nombre, precio FROM productos WHERE nombre = ?', [String(req.query.nombre)], (err, filas) => res.json(filas));
});

app.get('/ping', (req, res) => {
  // Arreglo 2: solo IPs, y execFile sin shell
  const host = String(req.query.host);
  if (net.isIP(host) === 0) return res.status(400).send('IP no válida');
  execFile('ping', ['-c', '1', host], (err, salida) => res.send(salida));
});

app.get('/factura', (req, res) => {
  // Arreglo 3: la ruta final tiene que quedar dentro de FACTURAS
  const ruta = path.resolve(FACTURAS, path.basename(String(req.query.archivo))); // njsscan-ignore: join_resolve_path_traversal
  if (!ruta.startsWith(FACTURAS + path.sep)) return res.status(404).end();
  res.send(fs.readFileSync(ruta, 'utf8')); // njsscan-ignore: generic_path_traversal, express_xss
});

app.post('/preferencias', express.json(), (req, res) => {
  const { tema, idioma } = req.body;
  res.json({ tema: String(tema), idioma: String(idioma) });
});

app.listen(3000);
"""


def paquete(lodash, express):
    return json.dumps({
        "name": "tienda", "version": "1.0.0", "private": True,
        "dependencies": dict(sorted({"express": express, "mysql2": "3.24.6", **({"lodash": lodash} if lodash else {})}.items())),
        "devDependencies": {"eslint": "10.13.0", "eslint-plugin-security": "4.2.0"},
    }, indent=2) + "\n"


ESLINT = """// eslint.config.js — solo las reglas de seguridad
const security = require('eslint-plugin-security');
module.exports = [security.configs.recommended];
"""

EJECUTAR_NODE = """#!/bin/sh
# Corre dentro de node:22-slim: eslint-plugin-security y npm audit.
set -u
cd /demo
for d in app app-arreglada; do (cd $d && npm install --no-audit --no-fund --loglevel=error >/dev/null 2>&1); done
echo "### versiones (node)"
node -v; echo "npm $(npm -v)"; (cd app && npx eslint --version; npm ls eslint-plugin-security --depth=0 | tail -n 2 | head -1)
echo
echo "### 3 · eslint-plugin-security sobre la app vulnerable"
echo "\\$ npx eslint ."
(cd app && npx eslint . 2>&1; echo "código de salida: $?")
echo "\\$ npx eslint . --max-warnings 0"
(cd app && npx eslint . --max-warnings 0 >/dev/null 2>&1; echo "código de salida: $?")
echo
echo "### 4 · npm audit sobre la app vulnerable (solo lo que se despliega)"
echo "\\$ npm audit --omit=dev"
(cd app && npm audit --omit=dev 2>&1; echo "código de salida: $?")
echo
echo "### 5 · el job del pipeline (npm audit --audit-level=high) sobre las dos versiones"
echo "\\$ npm audit --omit=dev --audit-level=high   # app"
(cd app && npm audit --omit=dev --audit-level=high >/dev/null 2>&1; echo "código de salida: $?")
echo "\\$ npm audit --omit=dev --audit-level=high   # app-arreglada"
(cd app-arreglada && npm audit --omit=dev --audit-level=high 2>&1 | tail -n 2; echo "código de salida: $?")
echo
echo "### 6 · eslint-plugin-security sobre la app arreglada"
(cd app-arreglada && npx eslint . 2>&1; echo "código de salida: $?")
"""

EJECUTAR_PY = """#!/bin/sh
# Corre dentro de python:3.13-slim: njsscan (por debajo usa semgrep y libsast).
set -u
pip install -q --root-user-action=ignore njsscan==1.0.1 >/dev/null 2>&1
cd /demo
echo "### versiones (njsscan)"
njsscan --version 2>&1 | tail -n 1
echo
echo "### 1 · njsscan sobre la app vulnerable"
echo "\\$ njsscan app/"
njsscan --exit-warning app/server.js 2>&1 | sed -n '/^╒\\|^│\\|^╞\\|^├\\|^╘/p' | grep -E 'RULE ID|SEVERITY|FILES|DESCRIPTION|^╒|^╞|^╘|server.js' | cut -c1-200
njsscan --exit-warning app/server.js >/dev/null 2>&1; echo "código de salida: $?"
echo
echo "### 1b · njsscan, solo los identificadores de regla"
njsscan --json app/server.js 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); [print(k, '·', v['metadata']['severity'], '·', ','.join(str(f['match_lines'][0]) for f in v['files'])) for k,v in sorted(d['nodejs'].items())]"
echo
echo "### 1c · ¿por qué no salió la inyección SQL? La misma consulta con mysql y con mysql2"
for m in mysql mysql2; do
  sed "s/require('mysql2')/require('$m')/" app/server.js > /tmp/con-$m.js
  printf '%s: ' "require('$m')"; njsscan --json /tmp/con-$m.js 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin)['nodejs']; print('node_sqli_injection' if 'node_sqli_injection' in d else 'sin node_sqli_injection')"
done
echo
echo "### 2 · njsscan sobre la app arreglada, SIN las anotaciones njsscan-ignore"
sed 's| // njsscan-ignore.*$||' app-arreglada/server.js > /tmp/arreglada-sin-anotar.js
njsscan --json /tmp/arreglada-sin-anotar.js 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); r=d['nodejs']; print(len(r), 'hallazgos'); [print(k, '·', v['metadata']['severity'], '· línea', v['files'][0]['match_lines'][0]) for k,v in sorted(r.items())]"
njsscan --exit-warning /tmp/arreglada-sin-anotar.js >/dev/null 2>&1; echo "código de salida: $?"
echo
echo "### 2b · njsscan sobre la app arreglada, CON las anotaciones (falsos positivos revisados)"
grep -n 'njsscan-ignore' app-arreglada/server.js
njsscan --json app-arreglada/server.js 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); r=d['nodejs']; print(len(r), 'hallazgos'); [print(k, '·', v['metadata']['severity']) for k,v in sorted(r.items())]"
njsscan --exit-warning app-arreglada/server.js >/dev/null 2>&1; echo "código de salida: $?"
"""

CORRER = """#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md. node_modules queda en volúmenes aparte.
cd "$(dirname "$0")"
D="$(pwd -W 2>/dev/null || pwd)"
{ echo '# Salida real — seguridad en el pipeline para Node.js'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ)."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" python:3.13-slim sh /demo/ejecutar-njsscan.sh
  echo
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" -v demo-node-mods-a:/demo/app/node_modules -v demo-node-mods-b:/demo/app-arreglada/node_modules node:22-slim sh /demo/ejecutar-node.sh
  echo '```'; } > SALIDA.md 2>&1
"""

W("app/server.js", VULN)
W("app/package.json", paquete("4.17.20", "4.17.1"))
W("app/eslint.config.js", ESLINT)
W("app-arreglada/server.js", ARREGLADA)
W("app-arreglada/package.json", paquete(None, "5.3.0"))
W("app-arreglada/eslint.config.js", ESLINT)
W("ejecutar-node.sh", EJECUTAR_NODE)
W("ejecutar-njsscan.sh", EJECUTAR_PY)
W("correr.sh", CORRER)
print("ok")
