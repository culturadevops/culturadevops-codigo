#!/usr/bin/env bash
# Leccion 4 — Codigos de salida: lo unico que tu script le cuenta al de fuera.
cd "$(mktemp -d)" || exit 1

echo "== 4.1 · El estado de una tuberia es el del ULTIMO comando =="
cat /no/existe 2>/dev/null | wc -l > /dev/null
echo "  cat /no/existe | wc -l   ->  codigo $?   <- el del wc, que fue bien"
cat /no/existe 2>/dev/null | wc -l > /dev/null
echo "  PIPESTATUS de esa misma tuberia: (${PIPESTATUS[*]})   <- el primero SI fallo"

echo
echo "== 4.2 · El clasico: guardar el log con tee =="
echo "  ./desplegar.sh | tee despliegue.log"
bash -c 'echo "  desplegando..."; exit 7' | tee despliegue.log > /dev/null
echo "  codigo: $?   <- el de tee. El 7 del script se perdio."
set -o pipefail
bash -c 'echo "  desplegando..."; exit 7' | tee despliegue.log > /dev/null
echo "  con set -o pipefail: $?   <- ahora si"
set +o pipefail

echo
echo "== 4.3 · LA TRAMPA: local se come el codigo =="
mal() { local salida=$(exit 9); echo "  local salida=\$(...)  ->  \$? = $?"; }
bien() { local salida; salida=$(exit 9); echo "  local y asignacion aparte -> \$? = $?"; }
mal
bien
echo "  'local' es un comando, y devuelve SU codigo. Declara primero, asigna despues."

echo
echo "== 4.4 · Comprobar de verdad, comando a comando =="
cat > paso.sh <<'FIN'
#!/usr/bin/env bash
paso() {
  local nombre="$1"; shift
  if "$@"; then
    echo "  [ok]    $nombre"
  else
    local c=$?
    echo "  [FALLO] $nombre (codigo $c)" >&2
    return "$c"
  fi
}
paso "construir"  true
paso "publicar"   bash -c 'exit 4'
paso "avisar"     true
FIN
bash paso.sh
echo "  codigo final del script: $(bash paso.sh >/dev/null 2>&1; echo $?)"
echo "  Ojo: sin 'exit' en el ultimo paso, el script sale con el codigo del ULTIMO comando."

echo
echo "== 4.5 · Codigos con significado =="
echo "  0   todo bien"
echo "  1   fallo generico"
echo "  2   lo llamaste mal"
echo "  64-78 convencion de sysexits.h (EX_USAGE=64, EX_UNAVAILABLE=69...)"
echo "  126 el archivo existe pero no es ejecutable · 127 no existe el comando"
bash -c 'comando_que_no_existe' 2>/dev/null
echo "  ejemplo real: $? para un comando que no existe"
echo "  130 lo mataste con Ctrl+C (128 + 2, la señal)"
