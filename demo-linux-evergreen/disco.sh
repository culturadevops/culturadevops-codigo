#!/bin/bash
# Demo «No space left on device» (cultura-devops, 2026-10-23). Corre DENTRO del contenedor.
# /datos es un tmpfs de 20 MB y /inodos uno de 50 MB con solo 200 inodos (los monta ejecutar.sh con --tmpfs).
# Todo lo que se llena y se borra vive en esos dos tmpfs: el contenedor y sus tmpfs desaparecen al final.
p() { echo "\$ $*"; eval "$@" 2>&1; echo; }

echo "### 1 · El error"
cd /datos || exit 1
p 'df -h /datos'
p 'dd if=/dev/zero of=backup.tar bs=1M count=30 status=none'
p 'echo "una línea más" >> app.log'
p 'df -h /datos'

echo "### 2 · Quién se comió el espacio"
mkdir -p logs cache
p 'du -sh /datos/* | sort -h'
p 'du -ah /datos | sort -h | tail -n 3'
p 'find /datos -type f -size +5M -exec ls -lh {} \;'
p 'rm backup.tar'
p 'df -h /datos'

echo "### 3 · Borré el fichero y el espacio no vuelve"
dd if=/dev/zero of=app.log bs=1M count=15 status=none
( exec 3>>/datos/app.log; exec sleep 600 ) &
sleep 0.5
p 'df -h /datos'
p 'rm app.log'
p 'ls -lh /datos'
p 'df -h /datos'
p 'lsof +L1 2>/dev/null | grep -E "COMMAND|/datos"'
PID=$(lsof -t +L1 2>/dev/null | head -1)
p "ls -l /proc/$PID/fd | grep datos"
echo "# Si no puedes reiniciar el proceso: vaciar el fichero abierto por su descriptor"
p ": > /proc/$PID/fd/3"
p 'df -h /datos'
kill "$PID" 2>/dev/null

echo "### 4 · Hay espacio, pero «No space left on device»"
cd /inodos || exit 1
p 'df -h /inodos'
p 'df -i /inodos'
p 'for i in $(seq 1 300); do echo x > "f$i" || { echo "falló en el fichero $i"; break; }; done'
p 'df -h /inodos'
p 'df -i /inodos'
p 'ls | wc -l'
