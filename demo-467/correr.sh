#!/usr/bin/env bash
# Demo del vídeo 467 «La puerta trasera de xz» — se EJECUTA y su salida va a SALIDA.md.
#   1) qué versión de xz/liblzma traen hoy varias imágenes de Linux (contenedores, nada se instala en la máquina);
#   2) un comprobador de 6 líneas: ¿es 5.6.0 o 5.6.1?
#   3) el comprobador probado contra las dos versiones afectadas escritas a mano (no se descarga nada malicioso).
# ⛔ Nunca se descarga xz 5.6.0/5.6.1: las versiones afectadas solo aparecen como texto.
set -u
comprobar() {   # $1 = salida de «xz --version»
  v=$(echo "$1" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
  case "$v" in
    5.6.0|5.6.1) echo "  xz $v -> AFECTADA (CVE-2024-3094)";;
    *)           echo "  xz $v -> no es 5.6.0 ni 5.6.1";;
  esac
}
# la puerta trasera estaba en la BIBLIOTECA liblzma, que está aunque no esté el programa xz
ingenuo() {   # mira solo el primer número de versión
  local v; v=$(echo "$1" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  case "$v" in 5.6.0|5.6.1) echo "  ingenuo:  $v -> AFECTADA";; "") echo "  ingenuo:  no instalada";; *) echo "  ingenuo:  $v -> no afectada";; esac
}
mejor() {     # si la versión dice «+reallyX», la de verdad es X (Debian/Ubuntu la usan para volver atrás)
  local v; v=$(echo "$1" | grep -oE 'really[0-9]+\.[0-9]+\.[0-9]+' | sed 's/really//')
  [ -z "$v" ] && v=$(echo "$1" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  case "$v" in 5.6.0|5.6.1) echo "  mejor:    $v -> AFECTADA";; "") echo "  mejor:    no instalada";; *) echo "  mejor:    $v -> no afectada";; esac
}
paquete() {   # $1 = imagen, $2 = comando que imprime la versión de liblzma
  echo "\$ docker run --rm $1 $2"
  v=$(MSYS_NO_PATHCONV=1 docker run --rm "$1" sh -c "$2" 2>/dev/null | head -1)
  echo "${v:-(nada)}"
  ingenuo "$v"
  mejor "$v"
  echo
}
paquete debian:12    "dpkg-query -W liblzma5"
paquete ubuntu:24.04 "dpkg-query -W liblzma5"
paquete alpine:3.20  "apk info -v 2>/dev/null | grep '^xz-libs'"
paquete fedora:41    "rpm -q xz-libs"
echo '$ # los dos comprobadores, contra las versiones afectadas (solo texto)'
for v in 5.6.0-0.2 5.6.1-1 5.6.1+really5.4.5-1 5.6.2-1; do echo "  versión: $v"; ingenuo "$v"; mejor "$v"; done
echo
echo '$ git ls-remote --tags https://github.com/tukaani-project/xz | grep -E "v5\.6\.[0-9]+$" | sed "s|.*/||"'
git ls-remote --tags https://github.com/tukaani-project/xz 2>/dev/null | grep -E "refs/tags/v5\.6\.[0-9]+$" | sed 's|.*/||' | sort -V
