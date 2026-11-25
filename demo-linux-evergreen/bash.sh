#!/bin/bash
# Demo «Bash scripting desde cero» (cultura-devops, 2026-10-23). Corre DENTRO del contenedor, todo en una carpeta de mktemp.
# Regla de la casa: ningún script de esta demo borra nada.
L=$(mktemp -d) && cd "$L" || exit 1
mostrar() { echo "\$ cat $1"; cat "$1"; echo; }
correr() { echo "\$ $*"; "$@" 2>&1; echo "(código de salida: $?)"; echo; }

echo "### 1 · El primer script"
cat > hola.sh <<'EOF'
#!/bin/bash
echo "Hola, $USER"
echo "Hoy es $(date +%A)"
EOF
chmod +x hola.sh
mostrar hola.sh
USER=ana correr ./hola.sh

echo "### 2 · Variables y comillas"
cat > variables.sh <<'EOF'
#!/bin/bash
nombre="mi servidor"
archivo="reporte final.txt"
echo "Revisando $nombre"
touch "$archivo"
ls -1
touch $archivo
ls -1
EOF
chmod +x variables.sh
mostrar variables.sh
correr ./variables.sh

echo "### 3 · Argumentos e if"
cat > edad.sh <<'EOF'
#!/bin/bash
if [[ $# -ne 1 ]]; then
  echo "uso: $0 <numero>" >&2
  exit 2
fi
if [[ $1 -ge 18 ]]; then
  echo "mayor de edad"
else
  echo "menor de edad"
fi
EOF
chmod +x edad.sh
mostrar edad.sh
correr ./edad.sh 20
correr ./edad.sh 12
correr ./edad.sh

echo "### 4 · Bucles"
cat > bucle.sh <<'EOF'
#!/bin/bash
for servidor in web1 web2 db1; do
  echo "comprobando $servidor"
done
for i in {1..3}; do
  echo "intento $i"
done
EOF
chmod +x bucle.sh
mostrar bucle.sh
correr ./bucle.sh

echo "### 5 · Funciones"
cat > funciones.sh <<'EOF'
#!/bin/bash
saludar() {
  local nombre=$1
  echo "Hola, $nombre"
}
saludar Ana
saludar "Luis Pérez"
EOF
chmod +x funciones.sh
mostrar funciones.sh
correr ./funciones.sh

echo "### 6 · Códigos de salida"
echo '$ ls existe-no.txt; echo $?'
ls existe-no.txt 2>&1; echo $?
echo '$ true; echo $?'
true; echo $?
echo

echo "### 7 · Sin set -euo pipefail"
cat > sin.sh <<'EOF'
#!/bin/bash
cp no-existe.conf /tmp/
echo "copiado, sigo como si nada"
echo "directorio: $DIRECTORIO_DESTINO/backups"
cat no-existe.log | sort
echo "la tubería terminó con $?"
EOF
chmod +x sin.sh
mostrar sin.sh
correr ./sin.sh

echo "### 8 · Con set -euo pipefail"
cat > con-e.sh <<'EOF'
#!/bin/bash
set -euo pipefail
cp no-existe.conf /tmp/
echo "esto ya no se imprime"
EOF
cat > con-u.sh <<'EOF'
#!/bin/bash
set -euo pipefail
echo "directorio: $DIRECTORIO_DESTINO/backups"
echo "esto ya no se imprime"
EOF
cat > con-pipefail.sh <<'EOF'
#!/bin/bash
set -euo pipefail
cat no-existe.log | sort
echo "esto ya no se imprime"
EOF
chmod +x con-*.sh
mostrar con-e.sh
correr ./con-e.sh
mostrar con-u.sh
correr ./con-u.sh
mostrar con-pipefail.sh
correr ./con-pipefail.sh

echo "### 9 · Un script que sirve: chequeo de salud"
mkdir -p app/logs
printf 'ok\n' > app/logs/app.log
cat > salud.sh <<'EOF'
#!/bin/bash
# Revisa disco, un fichero y un proceso. Sale con 1 si algo falla: listo para cron o para un pipeline.
set -euo pipefail
LIMITE=${LIMITE:-90}
fallos=0

revisar_disco() {
  local uso
  uso=$(df --output=pcent / | tail -1 | tr -dc '0-9')
  if (( uso >= LIMITE )); then
    echo "FALLO disco: ${uso}% (límite ${LIMITE}%)"; fallos=$((fallos + 1))
  else
    echo "ok    disco: ${uso}%"
  fi
}

revisar_fichero() {
  if [[ -s $1 ]]; then echo "ok    fichero: $1"; else echo "FALLO fichero: $1 no existe o está vacío"; fallos=$((fallos + 1)); fi
}

revisar_proceso() {
  if pgrep -x "$1" > /dev/null; then echo "ok    proceso: $1"; else echo "FALLO proceso: $1 no está corriendo"; fallos=$((fallos + 1)); fi
}

revisar_disco
revisar_fichero app/logs/app.log
revisar_fichero app/config.yml
revisar_proceso sleep

echo "fallos: $fallos"
exit $(( fallos > 0 ))
EOF
chmod +x salud.sh
mostrar salud.sh
sleep 120 &
correr ./salud.sh
echo "puerto: 8080" > app/config.yml
correr ./salud.sh
LIMITE=1 correr ./salud.sh
kill %1 2>/dev/null
