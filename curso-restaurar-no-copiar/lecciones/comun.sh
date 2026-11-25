# Lo que comparten las lecciones. Se carga con: source /curso/comun.sh
# Corre dentro del contenedor «operador»: PGHOST, PGUSER, PGPASSWORD y PGDATABASE ya vienen puestos.

export PGOPTIONS='-c client_min_messages=warning'

titulo() { printf '\n== %s ==\n' "$1"; }

# sembrar N: la tabla de pedidos, desde cero, con N filas.
sembrar() {
  psql -q -v ON_ERROR_STOP=1 <<SQL
DROP TABLE IF EXISTS pedidos;
CREATE TABLE pedidos (
  id      bigserial PRIMARY KEY,
  cliente text NOT NULL,
  total   numeric(10,2) NOT NULL,
  creado  timestamptz NOT NULL DEFAULT now()
);
INSERT INTO pedidos (cliente, total)
SELECT 'cliente-' || g, (g % 97) + 0.5 FROM generate_series(1, $1) g;
SQL
}

# filas BASE: cuántos pedidos hay en esa base de datos ("-" si ni siquiera existe la tabla).
filas() { psql -d "$1" -tAc "SELECT count(*) FROM pedidos" 2>/dev/null || echo "-"; }

bytes() { stat -c %s "$1"; }

# base_nueva NOMBRE: una base de datos vacía donde restaurar, sin tocar la original.
base_nueva() {
  psql -q -c "DROP DATABASE IF EXISTS $1 WITH (FORCE)" -c "CREATE DATABASE $1"
}

# ms: milisegundos desde el arranque del reloj (para cronometrar restauraciones).
ahora_ms() { date +%s%3N; }
