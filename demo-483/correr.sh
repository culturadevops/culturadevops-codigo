#!/usr/bin/env bash
# Demo del vídeo 483 «¿Debo aprender Linux en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# Un script de limpieza típico de lo que genera una IA: «borra los temporales de la app».
#   1) ShellCheck lo revisa sin ejecutarlo;
#   2) qué pasaría con la variable vacía: se IMPRIME el comando expandido con echo (NUNCA se ejecuta el rm), dentro
#      de un contenedor Debian desechable;
#   3) la versión revisada, ejecutada de verdad: con la variable vacía se detiene antes del rm, y con una carpeta
#      temporal (mktemp) borra solo lo que debe.
# Ver memoria «una demo destructiva nunca se ejecuta».
set -u
export MSYS_NO_PATHCONV=1
T=$(mktemp -d)
cd "$T"

cat > limpiar.sh <<'EOF'
#!/bin/bash
# Borra los temporales de la app
DIR=$APP_TMP
cd $DIR
rm -rf $DIR/*
echo "limpieza terminada"
EOF

cat > limpiar-revisado.sh <<'EOF'
#!/bin/bash
# Borra los temporales de la app
set -euo pipefail
DIR="${APP_TMP:?APP_TMP no está definida}"
cd -- "$DIR"
rm -rf -- "${DIR:?}"/*
echo "limpieza terminada en $DIR"
EOF

SC="docker run --rm -v $(cygpath -w "$T"):/mnt koalaman/shellcheck:v0.11.0"
echo '$ cat limpiar.sh   # típico de lo que genera una IA'
cat limpiar.sh
echo
echo '$ shellcheck limpiar.sh'
$SC /mnt/limpiar.sh 2>&1 | grep -E "^In |SC[0-9]{4}" | sed 's|/mnt/||'
echo
echo '$ # ¿y si APP_TMP llega vacía? (con echo delante: se imprime, NO se ejecuta)'
docker run --rm -v "$(cygpath -w "$T"):/mnt" debian:13.1-slim bash -c '
  sed "s/^rm /echo rm /" /mnt/limpiar.sh > /tmp/ensayo.sh
  APP_TMP="" bash /tmp/ensayo.sh 2>&1 | cut -c1-110
'
echo
echo '$ shellcheck limpiar-revisado.sh'
$SC /mnt/limpiar-revisado.sh 2>&1
echo "(código de salida: $($SC /mnt/limpiar-revisado.sh >/dev/null 2>&1; echo $?))"
echo
echo '$ APP_TMP="" bash limpiar-revisado.sh'
docker run --rm -v "$(cygpath -w "$T"):/mnt" debian:13.1-slim bash -c 'APP_TMP="" bash /mnt/limpiar-revisado.sh; echo "(código de salida: $?)"' 2>&1 | sed 's|/mnt/||'
echo
echo '$ # ahora con una carpeta temporal de verdad'
docker run --rm -v "$(cygpath -w "$T"):/mnt" debian:13.1-slim bash -c '
  D=$(mktemp -d); touch "$D/a.tmp" "$D/b.tmp"; echo "\$ ls \$APP_TMP"; ls "$D"
  echo "\$ bash limpiar-revisado.sh"; APP_TMP="$D" bash /mnt/limpiar-revisado.sh
  echo "\$ ls \$APP_TMP"; ls "$D"; echo "(vacía)"; echo "\$ ls / | head -3   # el sistema sigue intacto"; ls / | head -3
' 2>&1
echo
echo '$ shellcheck --version'
docker run --rm koalaman/shellcheck:v0.11.0 --version 2>&1 | grep "^version"
cd / && rm -rf "$T"
