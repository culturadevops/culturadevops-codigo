#!/usr/bin/env bash
# Lección 2 · El ensayo cronometrado: los dos números que nadie tiene.
#
#   RPO: cuántos datos pierdes (todo lo que se escribió después de la última copia).
#   RTO: cuánto tardas en volver (y crece con el tamaño, no con tus ganas).
# Aquí no se estiman: se destruye el original y se miden.
source /curso/comun.sh

titulo "2.1 · Lo que se pierde: una tienda que vende mientras se hace la copia"
sembrar 1000 >/dev/null
# La tienda: 10 pedidos por segundo, sin parar.
( while true; do psql -q -c "INSERT INTO pedidos (cliente, total) SELECT 'web', 9.99 FROM generate_series(1,1)" 2>/dev/null; sleep 0.1; done ) &
TIENDA=$!
sleep 2
pg_dump -Fc -f /copias/pedidos.dump tienda
echo "  copia hecha · la tienda sigue vendiendo 5 segundos más"
sleep 5
kill $TIENDA; wait $TIENDA 2>/dev/null
antes=$(filas tienda)
psql -q -c "DROP TABLE pedidos"   # el desastre: un DROP en la base de datos equivocada
base_nueva restaurada
pg_restore -d restaurada /copias/pedidos.dump
despues=$(filas restaurada)
echo "  pedidos justo antes del desastre: $antes"
echo "  pedidos en la copia restaurada:   $despues"
echo "  perdidos: $((antes - despues)), los de los últimos 5 segundos"

titulo "2.2 · Lo que se tarda: restaurar según el tamaño"
printf '  %-12s %10s %12s\n' "pedidos" "copia" "restaurar"
for n in 10000 100000 1000000; do
  sembrar $n >/dev/null
  psql -q -c "CREATE INDEX ON pedidos (cliente)" -c "CREATE INDEX ON pedidos (creado)"
  pg_dump -Fc -f /copias/t.dump tienda
  base_nueva restaurada
  t0=$(ahora_ms); pg_restore -d restaurada /copias/t.dump; t1=$(ahora_ms)
  printf '  %-12s %8s KB %9s ms\n' "$n" "$(( $(bytes /copias/t.dump) / 1024 ))" "$((t1 - t0))"
done

titulo "2.3 · El millón, restaurado con 4 procesos (pg_restore -j 4)"
base_nueva restaurada
t0=$(ahora_ms); pg_restore -j 4 -d restaurada /copias/t.dump; t1=$(ahora_ms)
echo "  1000000 pedidos con -j 4: $((t1 - t0)) ms · pedidos: $(filas restaurada)"
