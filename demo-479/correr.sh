#!/usr/bin/env bash
# Demo del vídeo 479 «¿Debo aprender ciberseguridad en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un login en Python como el que sale al pedirle a una IA «rápido, que funcione»: SQL armado con f-string, contraseña en el
# código y un comando con shell=True. 1) Se ataca de verdad, en local, con SQLite en memoria: entra sin contraseña.
# 2) bandit lo encuentra sin ejecutar. 3) Se arregla con parámetros y el ataque deja de entrar.
# 4) Paquetes inventados: se pregunta a PyPI si existen dos nombres reales y dos inventados (escritos por mí, imitando lo que alucina un modelo) (solo lectura; no se instala nada).
# Entorno virtual propio en un directorio temporal.
set -u
export PYTHONUTF8=1
T=$(mktemp -d)
cd "$T"
python -m venv .venv >/dev/null 2>&1
. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate
pip install -q bandit==1.8.6 >/dev/null 2>&1

cat > login.py <<'EOF'
import sqlite3
import subprocess
import sys

CLAVE_ADMIN = "SuperSecreta2026"


def preparar():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE usuarios (nombre TEXT, clave TEXT)")
    db.execute("INSERT INTO usuarios VALUES ('ana', 'x9!kL2')")
    return db


def entrar(db, nombre, clave):
    q = f"SELECT nombre FROM usuarios WHERE nombre = '{nombre}' AND clave = '{clave}'"
    return db.execute(q).fetchone()


def respaldo(carpeta):
    subprocess.run(f"tar czf respaldo.tgz {carpeta}", shell=True)


if __name__ == "__main__":
    db = preparar()
    fila = entrar(db, sys.argv[1], sys.argv[2])
    print("ENTRÓ como", fila[0] if fila else None) if fila else print("acceso denegado")
EOF

echo '$ python --version'; python --version
echo '$ grep -n "f\"SELECT" login.py'; grep -n 'f"SELECT' login.py
echo
echo '$ python login.py ana malaclave'
python login.py ana malaclave
echo "\$ python login.py \"ana' --\" cualquiera"
python login.py "ana' --" cualquiera
echo
echo '$ bandit -q login.py'
bandit -q login.py 2>&1 | grep -E "Issue:|Severity:|Location:" | sed 's/^ *//'
echo '$ grep -n CLAVE_ADMIN login.py   # la contraseña escrita en el código: bandit no la marcó'
grep -n "CLAVE_ADMIN =" login.py
sed 's/CLAVE_ADMIN/PASSWORD_ADMIN/' login.py > login_en.py
echo '$ # la misma línea, con la variable en inglés'
echo '$ bandit -q login_en.py | grep B105'
bandit -q login_en.py 2>&1 | grep -A2 "B105" | grep -E "Issue:|Location:" | sed 's/^ *//'
echo
# el arreglo: parámetros en la consulta, la clave fuera del código, sin shell
sed -i "s|    q = f\"SELECT nombre FROM usuarios WHERE nombre = '{nombre}' AND clave = '{clave}'\"|    q = \"SELECT nombre FROM usuarios WHERE nombre = ? AND clave = ?\"|; s|    return db.execute(q).fetchone()|    return db.execute(q, (nombre, clave)).fetchone()|; s|^CLAVE_ADMIN = .*|import os\nCLAVE_ADMIN = os.environ.get(\"CLAVE_ADMIN\")|; s|    subprocess.run(f\"tar czf respaldo.tgz {carpeta}\", shell=True)|    subprocess.run([\"tar\", \"czf\", \"respaldo.tgz\", carpeta], check=True)|" login.py
echo '$ # arreglo: consulta con parámetros (?), clave en variable de entorno, subprocess sin shell'
echo "\$ python login.py \"ana' --\" cualquiera"
python login.py "ana' --" cualquiera
echo '$ python login.py ana x9!kL2'
python login.py ana 'x9!kL2'
echo '$ bandit -q login.py'
bandit -q login.py 2>&1 | grep -E "Issue:|Severity:" | sed 's/^ *//'
echo "(código de salida de bandit: $(bandit -q -lll login.py >/dev/null 2>&1; echo $?) con -lll, solo severidad alta)"
echo
echo '$ # ¿existen en PyPI? dos reales y dos nombres inventados, del tipo que alucina un modelo'
for p in requests flask-login flask-secure-login-helper sqlite3-safe-query; do
  c=$(curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/$p/json")
  [ "$c" = "200" ] && echo "$p: existe" || echo "$p: NO EXISTE (HTTP $c)"
done
echo '$ bandit --version'
bandit --version 2>&1 | head -1
deactivate 2>/dev/null
cd / && rm -rf "$T"
