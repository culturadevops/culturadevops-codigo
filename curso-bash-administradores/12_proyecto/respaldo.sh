#!/usr/bin/env bash
#
# respaldo.sh — copia de seguridad de una carpeta, con todo lo del curso dentro.
#
#   respaldo.sh --origen /srv/tienda/datos --destino /copias [--conservar 3] [--dry-run]
#
# Codigos de salida: 0 hecho · 1 fallo · 2 lo llamaste mal · 75 hay otra copia en curso
#
set -euo pipefail
IFS=$'\n\t'

PROGRAMA=${0##*/}
CONSERVAR=3
DRY_RUN=0
ORIGEN=""
DESTINO=""

log()   { printf '%s  %s\n' "$(date -u '+%H:%M:%S')" "$*" >&2; }   # a stderr (leccion 4)
morir() { log "ERROR: $1"; exit "${2:-1}"; }          # $1 es el mensaje, $2 el codigo
uso()   { sed -n '3,7p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --origen)    ORIGEN="${2:?falta la ruta de --origen}"; shift 2 ;;
    --destino)   DESTINO="${2:?falta la ruta de --destino}"; shift 2 ;;
    --conservar) CONSERVAR="${2:?falta el numero}"; shift 2 ;;
    --dry-run)   DRY_RUN=1; shift ;;
    -h|--help)   uso ;;
    *)           log "opcion desconocida: $1"; uso ;;
  esac
done

# 1 · lo obligatorio, y todo de una vez (leccion 5)
faltan=()
[[ -n $ORIGEN  ]] || faltan+=(--origen)
[[ -n $DESTINO ]] || faltan+=(--destino)
[[ ${#faltan[@]} -eq 0 ]] || morir "faltan opciones: $(IFS=" "; echo "${faltan[*]}")" 2
[[ -d $ORIGEN ]]  || morir "el origen no es un directorio: $ORIGEN" 2
[[ $CONSERVAR =~ ^[0-9]+$ ]] || morir "--conservar tiene que ser un numero: $CONSERVAR" 2
(( CONSERVAR >= 1 )) || morir "--conservar tiene que ser 1 o mas" 2

mkdir -p "$DESTINO"

# 2 · cerrojo: uno a la vez. mkdir es atomico: o lo creas tu, o ya estaba.
CERROJO="$DESTINO/.respaldo.lock"
if ! mkdir "$CERROJO" 2>/dev/null; then
  morir "ya hay una copia en curso ($CERROJO)" 75
fi

# 3 · limpieza pase lo que pase (leccion 9)
TRABAJO=""
limpiar() {
  local codigo=$?
  [[ -n $TRABAJO && -d $TRABAJO ]] && rm -rf "$TRABAJO"
  rmdir "$CERROJO" 2>/dev/null || true
  (( codigo != 0 )) && log "salgo con codigo $codigo"
  return 0
}
trap limpiar EXIT
trap 'log "me han pedido parar"; exit 130' INT TERM

SELLO=$(date -u '+%Y%m%dT%H%M%SZ')
NOMBRE="respaldo-$SELLO.tar.gz"
TRABAJO=$(mktemp -d "$DESTINO/.trabajo.XXXXXX")

if (( DRY_RUN )); then
  log "[dry-run] copiaria $ORIGEN -> $DESTINO/$NOMBRE"
  log "[dry-run] conservaria las $CONSERVAR mas recientes"
  # el || true importa: con pipefail, un ls sin resultados tumbaria el script
  { ls -1t "$DESTINO"/respaldo-*.tar.gz 2>/dev/null || true; } | tail -n +$((CONSERVAR + 1)) |
    while IFS= read -r v; do log "[dry-run] borraria ${v##*/}"; done
  exit 0
fi

log "copiando $ORIGEN"
# El tar va a un temporal: si falla a mitad, no queda una copia rota con nombre bueno.
if ! tar -czf "$TRABAJO/$NOMBRE" -C "$ORIGEN" . 2>"$TRABAJO/error"; then
  log "tar fallo: $(head -1 "$TRABAJO/error")"
  exit 1
fi
mv "$TRABAJO/$NOMBRE" "$DESTINO/$NOMBRE"          # aparece entera o no aparece
TAM=$(du -k "$DESTINO/$NOMBRE" | cut -f1)
log "hecha: $NOMBRE (${TAM} KB)"

# 4 · comprobar que la copia se puede leer. Una copia sin probar no es una copia.
if ! tar -tzf "$DESTINO/$NOMBRE" >/dev/null 2>&1; then
  log "la copia no se puede leer: la borro"
  rm -f "$DESTINO/$NOMBRE"
  exit 1
fi
log "verificada: $(tar -tzf "$DESTINO/$NOMBRE" | wc -l) entradas"

# 5 · rotacion: conservar N, y nunca borrar la de hoy
sobran=$(ls -1t "$DESTINO"/respaldo-*.tar.gz 2>/dev/null | tail -n +$((CONSERVAR + 1)) || true)
if [[ -n $sobran ]]; then
  while IFS= read -r viejo; do
    [[ $viejo == "$DESTINO/$NOMBRE" ]] && continue
    rm -f -- "$viejo"
    log "rotacion: borrada ${viejo##*/}"
  done <<< "$sobran"
fi
log "copias que quedan: $(ls -1 "$DESTINO"/respaldo-*.tar.gz 2>/dev/null | wc -l)"
