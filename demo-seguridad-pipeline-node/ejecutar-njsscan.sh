#!/bin/sh
# Corre dentro de python:3.13-slim: njsscan (por debajo usa semgrep y libsast).
set -u
pip install -q --root-user-action=ignore njsscan==1.0.1 >/dev/null 2>&1
cd /demo
echo "### versiones (njsscan)"
njsscan --version 2>&1 | tail -n 1
echo
echo "### 1 · njsscan sobre la app vulnerable"
echo "\$ njsscan app/"
njsscan --exit-warning app/server.js 2>&1 | sed -n '/^╒\|^│\|^╞\|^├\|^╘/p' | grep -E 'RULE ID|SEVERITY|FILES|DESCRIPTION|^╒|^╞|^╘|server.js' | cut -c1-200
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
