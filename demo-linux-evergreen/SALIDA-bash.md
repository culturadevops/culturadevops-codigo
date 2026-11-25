# SALIDA — bash (cultura-devops, tanda evergreen de Linux)

> Corrida del 2026-10-23 12:51 en un contenedor: Ubuntu 24.04.4 LTS, GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu).

```
### 1 · El primer script
$ cat hola.sh
#!/bin/bash
echo "Hola, $USER"
echo "Hoy es $(date +%A)"

$ ./hola.sh
Hola, ana
Hoy es Friday
(código de salida: 0)

### 2 · Variables y comillas
$ cat variables.sh
#!/bin/bash
nombre="mi servidor"
archivo="reporte final.txt"
echo "Revisando $nombre"
touch "$archivo"
ls -1
touch $archivo
ls -1

$ ./variables.sh
Revisando mi servidor
hola.sh
reporte final.txt
variables.sh
final.txt
hola.sh
reporte
reporte final.txt
variables.sh
(código de salida: 0)

### 3 · Argumentos e if
$ cat edad.sh
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

$ ./edad.sh 20
mayor de edad
(código de salida: 0)

$ ./edad.sh 12
menor de edad
(código de salida: 0)

$ ./edad.sh
uso: ./edad.sh <numero>
(código de salida: 2)

### 4 · Bucles
$ cat bucle.sh
#!/bin/bash
for servidor in web1 web2 db1; do
  echo "comprobando $servidor"
done
for i in {1..3}; do
  echo "intento $i"
done

$ ./bucle.sh
comprobando web1
comprobando web2
comprobando db1
intento 1
intento 2
intento 3
(código de salida: 0)

### 5 · Funciones
$ cat funciones.sh
#!/bin/bash
saludar() {
  local nombre=$1
  echo "Hola, $nombre"
}
saludar Ana
saludar "Luis Pérez"

$ ./funciones.sh
Hola, Ana
Hola, Luis Pérez
(código de salida: 0)

### 6 · Códigos de salida
$ ls existe-no.txt; echo $?
ls: cannot access 'existe-no.txt': No such file or directory
2
$ true; echo $?
0

### 7 · Sin set -euo pipefail
$ cat sin.sh
#!/bin/bash
cp no-existe.conf /tmp/
echo "copiado, sigo como si nada"
echo "directorio: $DIRECTORIO_DESTINO/backups"
cat no-existe.log | sort
echo "la tubería terminó con $?"

$ ./sin.sh
cp: cannot stat 'no-existe.conf': No such file or directory
copiado, sigo como si nada
directorio: /backups
cat: no-existe.log: No such file or directory
la tubería terminó con 0
(código de salida: 0)

### 8 · Con set -euo pipefail
$ cat con-e.sh
#!/bin/bash
set -euo pipefail
cp no-existe.conf /tmp/
echo "esto ya no se imprime"

$ ./con-e.sh
cp: cannot stat 'no-existe.conf': No such file or directory
(código de salida: 1)

$ cat con-u.sh
#!/bin/bash
set -euo pipefail
echo "directorio: $DIRECTORIO_DESTINO/backups"
echo "esto ya no se imprime"

$ ./con-u.sh
./con-u.sh: line 3: DIRECTORIO_DESTINO: unbound variable
(código de salida: 1)

$ cat con-pipefail.sh
#!/bin/bash
set -euo pipefail
cat no-existe.log | sort
echo "esto ya no se imprime"

$ ./con-pipefail.sh
cat: no-existe.log: No such file or directory
(código de salida: 1)

### 9 · Un script que sirve: chequeo de salud
$ cat salud.sh
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

$ ./salud.sh
ok    disco: 30%
ok    fichero: app/logs/app.log
FALLO fichero: app/config.yml no existe o está vacío
ok    proceso: sleep
fallos: 1
(código de salida: 1)

$ ./salud.sh
ok    disco: 30%
ok    fichero: app/logs/app.log
ok    fichero: app/config.yml
ok    proceso: sleep
fallos: 0
(código de salida: 0)

$ ./salud.sh
FALLO disco: 30% (límite 1%)
ok    fichero: app/logs/app.log
ok    fichero: app/config.yml
ok    proceso: sleep
fallos: 1
(código de salida: 1)

```
