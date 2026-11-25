#!/usr/bin/env bash
# Leccion 7 — Arrays y argumentos: donde se pierden los espacios de verdad.
cd "$(mktemp -d)" || exit 1

echo "== 7.1 · Una lista de opciones en una variable de texto =="
OPCIONES="--config /etc/mi app.conf --verbose"
echo "  OPCIONES=\"$OPCIONES\"   (la ruta tiene un espacio)"
printf '  como texto, bash ve %d palabras:\n' "$(set -- $OPCIONES; echo $#)"
# shellcheck disable=SC2086
set -- $OPCIONES; for a in "$@"; do echo "    <$a>"; done

echo
echo "== 7.2 · Con un array, cada elemento es un argumento =="
OPC=(--config "/etc/mi app.conf" --verbose)
echo "  OPC=(--config \"/etc/mi app.conf\" --verbose)"
echo "  elementos: ${#OPC[@]}"
for a in "${OPC[@]}"; do echo "    <$a>"; done

echo
echo "== 7.3 · LA TRAMPA: \${OPC[@]} sin comillas, y \${OPC[*]} =="
echo '  "${OPC[@]}"  -> cada elemento, UN argumento (lo que quieres casi siempre)'
for a in ${OPC[@]}; do echo "    sin comillas: <$a>"; done
for a in "${OPC[*]}"; do echo "    con [*]:      <$a>   <- todo junto en uno"; done

echo
echo "== 7.4 · Lo mismo con los argumentos del script =="
cat > eco.sh <<'FIN'
#!/usr/bin/env bash
echo "  recibidos: $#"
echo '  con "$@": ' ; for a in "$@"; do echo "    <$a>"; done
echo '  con $* (sin comillas):'; for a in $*; do echo "    <$a>"; done
FIN
bash eco.sh --mensaje "todo bien" --destino /tmp

echo
echo "== 7.5 · Construir un comando a trozos, sin eval =="
CMD=(tar -czf copia.tar.gz)
[[ -d /etc/nginx ]] && CMD+=(--exclude '*.tmp')
CMD+=(servidores.txt)
printf 'web-01\n' > servidores.txt
echo "  comando: ${CMD[*]}"
"${CMD[@]}" 2>/dev/null && echo "  hecho: $(ls -l copia.tar.gz | awk '{print $5}') bytes"
echo "  Un array se va llenando segun las condiciones y se ejecuta entrecomillado."
echo "  eval con texto es lo que abre la puerta a que un nombre raro ejecute comandos."

echo
echo "== 7.6 · Arrays asociativos (bash 4+) =="
declare -A PUERTO=([web]=8080 [api]=9000 [db]=5432)
for s in "${!PUERTO[@]}"; do echo "  $s -> ${PUERTO[$s]}"; done
echo "  claves: \${!PUERTO[@]} · valores: \${PUERTO[@]} · y no tienen orden garantizado"
