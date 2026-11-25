#!/usr/bin/env bash
# Leccion 10 — Lanzar cosas a la vez sin perder los codigos de salida.
cd "$(mktemp -d)" || exit 1

cat > chequear.sh <<'FIN'
#!/usr/bin/env bash
sleep 0.4
[[ $1 == web-03 ]] && exit 1     # este servidor esta caido
echo "  $1 ok"
FIN

SERVIDORES=(web-01 web-02 web-03 web-04 web-05 web-06)
ahora_ms() { date +%s%3N; }
desde()    { echo "$(( $(ahora_ms) - $1 )) ms"; }

echo "== 10.1 · Uno detras de otro =="
t0=$(ahora_ms)
for s in "${SERVIDORES[@]}"; do bash chequear.sh "$s"; done
echo "  ${#SERVIDORES[@]} chequeos de 0,4 s en fila: $(desde "$t0")"

echo
echo "== 10.2 · LA TRAMPA: & sin wait =="
cat > sin_wait.sh <<'FIN'
#!/usr/bin/env bash
for s in web-01 web-02 web-03; do bash chequear.sh "$s" & done
echo "  todos los chequeos: OK"       # se imprime ANTES de que terminen
FIN
bash sin_wait.sh 2>&1 | sed 's/^/  /'
echo "  El script dijo OK y se fue. Los procesos hijos seguian corriendo."

echo
echo "== 10.3 · & y wait, recogiendo cada codigo =="
t0=$(ahora_ms)
declare -A PID_DE
for s in "${SERVIDORES[@]}"; do
  bash chequear.sh "$s" &
  PID_DE[$!]=$s
done
fallos=0
for pid in "${!PID_DE[@]}"; do
  if ! wait "$pid"; then
    echo "  CAIDO: ${PID_DE[$pid]}"
    fallos=$((fallos + 1))
  fi
done
echo "  todos a la vez: $(desde "$t0") · caidos: $fallos"
echo "  'wait \$pid' devuelve el codigo de ESE proceso. Un 'wait' pelado solo espera."

echo
echo "== 10.4 · Con limite, para no tumbar lo que ibas a medir =="
t0=$(ahora_ms)
printf '%s\n' "${SERVIDORES[@]}" | xargs -P 2 -I{} bash chequear.sh {} > /dev/null 2>&1
echo "  con xargs -P 2 (de dos en dos): $(desde "$t0")"
echo "  xargs -P N es el semaforo mas corto que hay. Y -I{} evita partir por espacios."
echo "  Ojo: xargs devuelve 123 si algun comando fallo, no el codigo del comando."
printf '%s\n' "${SERVIDORES[@]}" | xargs -P 2 -I{} bash chequear.sh {} > /dev/null 2>&1
echo "  codigo de xargs: $?"

echo
echo "== 10.5 · La salida de varios procesos se mezcla =="
echo "  Dos procesos escribiendo a la vez pueden partirse una linea por la mitad."
echo "  Cada uno a su archivo, y se juntan al final:"
for s in web-01 web-02; do bash chequear.sh "$s" > "salida.$s.txt" 2>&1 & done
wait
for f in salida.*.txt; do echo "    $f: $(cat "$f")"; done
