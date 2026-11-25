#!/usr/bin/env bash
# demo.sh — la corrida entera del vídeo 223.
#
# Se ejecuta DENTRO de un contenedor privilegiado, que hace de máquina Linux con permisos de
# administrador. Lo que se demuestra:
#
#   1. el rootfs: un contenedor no descarga magia, descomprime un tar
#   2. el ENOENT que NO es un fichero que falta, sino un cargador
#   3. el contenedor funcionando: PID 1, hostname propio, /proc propio
#   4. que el aislamiento es de verdad: ni ve ni puede matar lo de fuera
#   5. y lo que NO aísla, que es la mitad honesta del vídeo
#
# ⚠️ En los pasos 4 y 5 se pone CALLADO=1: ahí solo interesa la salida del programa de DENTRO,
#    y la narración del contenedorcito se mezclaba con ella hasta hacerla ilegible.
set -u

echo "== 1 · EL ROOTFS: un contenedor no baja magia, descomprime un tar =="
mkdir -p /rootfs && tar -xf /w/alpine-rootfs.tar -C /rootfs 2>/dev/null
echo -n "   ficheros en el rootfs: "; find /rootfs -type f 2>/dev/null | wc -l
echo -n "   tamaño en disco:       "; du -sh /rootfs 2>/dev/null | cut -f1
echo "   primer nivel:"
ls /rootfs | tr '\n' ' ' | fold -sw 62 | sed 's/^/     /'
echo "   ^ eso es una imagen de Alpine: un tar con un sistema de ficheros dentro."

echo
echo "== 2 · EL ENOENT QUE PARECE UN FICHERO QUE FALTA Y NO LO ES =="
mkdir -p /vacio/bin && cp /bin/ls /vacio/bin/
echo -n "   ¿está el binario dentro del chroot vacío?  "
[ -f /vacio/bin/ls ] && echo "SÍ, ahí está, $(stat -c%s /vacio/bin/ls) bytes" || echo "no"
python3 /w/contenedorcito.py /vacio /bin/ls 2>&1 | sed 's/^/   /'
echo -n "   y lo que le falta de verdad: "
ldd /bin/ls 2>/dev/null | head -2 | tr '\n' ' '
echo
echo "   ^ nada de eso existe dentro del chroot. Por eso ENOENT."

echo
echo "== 3 · Y AHORA CON UN ROOTFS DE VERDAD =="
python3 /w/contenedorcito.py /rootfs /bin/busybox sh -c '
echo "--- ya estoy dentro ---"
echo -n "me veo como PID: "; echo $$
echo    "hostname:        $(hostname)"
echo    "procesos que veo desde dentro:"
ps -o pid,comm 2>/dev/null | head -5
echo -n "raiz del sistema de ficheros: "; ls / | tr "\n" " "; echo
' 2>&1 | sed 's/^/   /'

echo
echo "== 4 · ¿EL AISLAMIENTO ES DE VERDAD? =="
sleep 300 &
FUERA=$!
echo "   el de FUERA arranca un proceso con PID $FUERA."
CALLADO=1 python3 /w/contenedorcito.py /rootfs /bin/busybox sh -c "
echo -n '   ¿lo VE el de dentro?    '
ps -o pid 2>/dev/null | grep -qw $FUERA && echo 'SI (mal)' || echo 'NO'
echo -n '   ¿puede MATARLO?         '
kill -9 $FUERA 2>/dev/null && echo 'SI (mal)' || echo 'NO: para el, ese PID no existe'
" 2>&1
echo -n "   ¿sigue vivo el de fuera? "; kill -0 $FUERA 2>/dev/null && echo "SÍ" || echo "no"
kill -9 $FUERA 2>/dev/null; wait $FUERA 2>/dev/null

echo
echo "== 5 · LO QUE NO AÍSLA (la mitad honesta del vídeo) =="
echo    "   núcleo que ve el de FUERA:  $(uname -r)"
echo -n "   núcleo que ve el de DENTRO: "
CALLADO=1 python3 /w/contenedorcito.py /rootfs /bin/busybox uname -r 2>&1
echo "   ^ EL MISMO. No hay máquina virtual: es UN núcleo repartido, y de ahí sale que un"
echo "     fallo del núcleo se lleve por delante a todos los contenedores de la máquina."
echo -n "   memoria que cree tener el de FUERA:  "; head -1 /proc/meminfo | tr -s ' '
echo -n "   memoria que cree tener el de DENTRO: "
CALLADO=1 python3 /w/contenedorcito.py /rootfs /bin/busybox head -1 /proc/meminfo 2>&1 | tr -s ' '
echo "   ^ la de la máquina entera. Los namespaces NO limitan recursos: eso son los cgroups,"
echo "     que es otra cosa distinta y NO está en este programa."
echo -n "   usuario que soy dentro: "
CALLADO=1 python3 /w/contenedorcito.py /rootfs /bin/busybox id -u 2>&1
echo "   ^ cero: root. Sin namespace de usuario, el root de dentro es el root de fuera."
