#!/usr/bin/env bash
# Lección 1 · La copia que vale 20 bytes.
#
# La línea de copia más copiada de internet: pg_dump | gzip > copia.gz. En la terminal funciona.
# En cron, el entorno viene vacío: no hay PGPASSWORD. pg_dump falla... y el código de salida de
# una tubería es el del ÚLTIMO comando, gzip, que comprimió nada y dice 0. La copia «se hizo».
source /curso/comun.sh
sembrar 1000 >/dev/null
rm -f /copias/*.gz

titulo "1.1 · La copia de siempre, desde tu terminal"
pg_dump tienda | gzip > /copias/terminal.sql.gz
echo "  código de salida: $? · tamaño: $(bytes /copias/terminal.sql.gz) bytes"

titulo "1.2 · La misma línea, desde cron (entorno vacío: sin PGPASSWORD)"
env -i PATH=/usr/bin:/bin HOME=/root PGHOST=db PGUSER=admin \
  bash -c 'pg_dump tienda | gzip > /copias/cron.sql.gz; echo "  código de salida: $?"' 2>&1 \
  | sed 's/^pg_dump:/  pg_dump:/'
echo "  tamaño: $(bytes /copias/cron.sql.gz) bytes"
gzip -t /copias/cron.sql.gz && echo "  gzip -t: el fichero está «bien» (es un gzip válido... de nada)"

titulo "1.3 · El día que hace falta: restaurar la copia de cron"
base_nueva restaurada
gunzip -c /copias/cron.sql.gz | psql -q -d restaurada
echo "  psql: código de salida $? · pedidos restaurados: $(filas restaurada)"

titulo "1.4 · Lo correcto: set -o pipefail, y comprobar que la copia tiene algo"
env -i PATH=/usr/bin:/bin HOME=/root PGHOST=db PGUSER=admin bash -c '
  set -o pipefail
  pg_dump tienda 2>/dev/null | gzip > /copias/cron2.sql.gz
  echo "  con pipefail -> código de salida: $?"'
minimo=1024
for f in /copias/terminal.sql.gz /copias/cron.sql.gz; do
  t=$(bytes "$f")
  if [ "$t" -lt "$minimo" ]; then
    echo "  $(basename "$f"): $t bytes < $minimo -> ALARMA: la copia está vacía"
  else
    echo "  $(basename "$f"): $t bytes -> ok"
  fi
done
