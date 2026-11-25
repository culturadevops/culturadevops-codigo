#!/usr/bin/env bash
# Leccion 5 — Comparar: [ ] y [[ ]] no son lo mismo, y los numeros no se comparan con <.
cd "$(mktemp -d)" || exit 1

echo "== 5.1 · Numeros y texto se comparan con operadores distintos =="
A=10; B=9
[[ $A -gt $B ]] && echo "  [[ \$A -gt \$B ]]  ->  10 > 9, correcto"
[[ "$A" > "$B" ]] || echo "  [[ \"\$A\" > \"\$B\" ]]  ->  FALSO: como texto, '10' va antes que '9'"
echo "  -gt -lt -eq -ne para numeros · > < == para texto"
(( A > B )) && echo "  (( A > B ))  ->  correcto, y aqui no hacen falta los dolares"

echo
echo "== 5.2 · LA TRAMPA: la variable vacia rompe [ ] =="
VACIA=
if [ $VACIA = "produccion" ]; then :; fi 2>/dev/null
echo "  [ \$VACIA = \"produccion\" ]  ->  $(bash -c '[ $VACIA = "produccion" ]' 2>&1 | head -1)"
echo "  (se convierte en [ = \"produccion\" ], que ni es una comparacion)"
if [ "$VACIA" = "produccion" ]; then echo mal; else echo "  con comillas: compara y dice que no. Bien."; fi
if [[ $VACIA == "produccion" ]]; then echo mal; else echo "  con [[ ]]: tampoco hace falta comillas. Bien."; fi

echo
echo "== 5.3 · Lo que [[ ]] hace y [ ] no =="
RAMA="feature/pago-tarjeta"
[[ $RAMA == feature/* ]] && echo "  patron:  [[ \$RAMA == feature/* ]]"
[[ $RAMA =~ ^feature/([a-z-]+)$ ]] && echo "  regex:   \${BASH_REMATCH[1]} = ${BASH_REMATCH[1]}"
[[ -f /etc/passwd && -r /etc/passwd ]] || echo "  && y || dentro: [[ -f x && -r x ]] (en [ ] hay que usar -a, que es peor)"
echo "  [ ] es un PROGRAMA (de hecho existe /usr/bin/[). [[ ]] lo interpreta bash."

echo
echo "== 5.4 · Comprobaciones de archivos que se usan a diario =="
touch archivo.txt; mkdir carpeta; ln -s archivo.txt enlace.txt 2>/dev/null
for prueba in "-e archivo.txt" "-f archivo.txt" "-d carpeta" "-s archivo.txt" "-r archivo.txt" "-x archivo.txt"; do
  # shellcheck disable=SC2086
  if [ $prueba ]; then r="si"; else r="no"; fi
  echo "  [ $prueba ]  ->  $r"
done
echo "  -e existe · -f es archivo normal · -d directorio · -s no esta vacio · -r legible · -x ejecutable"

echo
echo "== 5.5 · Valores por omision, que ahorran la mitad de los if =="
unset ENTORNO
echo "  \${ENTORNO:-produccion}   ->  ${ENTORNO:-produccion}   (usa el valor si esta)"
echo "  \${ENTORNO:=produccion}   ->  ${ENTORNO:=produccion}   (y ademas lo asigna: ENTORNO=$ENTORNO)"
unset TOKEN
echo "  \${TOKEN:?falta el token}  ->  $(bash -c 'echo "${TOKEN:?falta el token}"' 2>&1 | sed 's/.*: //')"
echo "  \${RUTA:+--ruta \$RUTA}    ->  solo pone el argumento si la variable tiene algo"
