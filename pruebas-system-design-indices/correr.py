# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: índices, lo que aceleran y lo que cuestan» (cultura-devops, 348).

PostgreSQL 17 (y 18 para el índice compuesto, que estrena «skip scan») en Docker. Una tabla de pedidos
con 2.000.000 de filas generadas con generate_series. Cada consulta se ejecuta 5 veces y se da la
mediana del «Execution Time» de EXPLAIN ANALYZE; el plan es el de la última.

  1 sin índice / con índice · 2 lo que ocupa y lo que tarda en crearse · 3 poca selectividad
  4 compuesto en el orden equivocado (17 y 18) · 5 función sobre la columna · 6 LIKE
  7 inserciones por segundo con 0, 1, 3 y 6 índices

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import re
import statistics
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
salida = []
FILAS = 2_000_000

TABLA = f"""
DROP TABLE IF EXISTS pedidos;
CREATE TABLE pedidos (
  id         bigserial PRIMARY KEY,
  cliente_id int         NOT NULL,
  estado     text        NOT NULL,
  creado     timestamptz NOT NULL,
  email      text        NOT NULL,
  total      numeric(10,2) NOT NULL
);
SELECT setseed(0.42);
INSERT INTO pedidos (cliente_id, estado, creado, email, total)
SELECT (random() * 99999)::int + 1,
       CASE WHEN r < 0.80 THEN 'entregado' WHEN r < 0.95 THEN 'enviado' ELSE 'pendiente' END,
       timestamptz '2026-10-01' - random() * interval '1095 days',
       'Cliente' || g || '@correo.test',
       round((random() * 500)::numeric, 2)
FROM (SELECT g, random() AS r FROM generate_series(1, {FILAS}) g) s;
VACUUM ANALYZE pedidos;
"""


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


class PG:
    def __init__(self, imagen, nombre):
        self.n = nombre
        docker("rm", "-f", nombre)
        docker("run", "-d", "--name", nombre, "-e", "POSTGRES_PASSWORD=lab", "--shm-size", "512m",
               "--tmpfs", "/var/lib/postgresql:size=4g", imagen,
               "-c", "shared_buffers=512MB", "-c", "max_parallel_workers_per_gather=0", "-c", "max_wal_size=8GB", check=True)
        # el entrypoint arranca un servidor temporal para el init y lo reinicia: se espera al definitivo
        for _ in range(240):
            if "init process complete" in docker("logs", nombre):
                break
            time.sleep(0.5)
        for _ in range(60):
            if "aceptando" in docker("exec", nombre, "psql", "-U", "postgres", "-tAc", "SELECT 'aceptando'"):
                break
            time.sleep(0.5)
        self.version = docker("exec", nombre, "psql", "-U", "postgres", "-tAc", "SHOW server_version")

    def sql(self, q):
        return docker("exec", "-i", self.n, "psql", "-U", "postgres", "-v", "ON_ERROR_STOP=1", "-tA", "-c", q, check=True)

    def guion(self, q):
        r = subprocess.run(["docker", "exec", "-i", self.n, "psql", "-U", "postgres", "-v", "ON_ERROR_STOP=1", "-q"],
                           input=q, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
        if r.returncode:
            raise SystemExit(f"[X] psql: {r.stderr}")
        return r.stdout

    def cronometrar(self, q):
        """Segundos de reloj que tarda una sentencia (con \\timing de psql)."""
        out = self.guion("\\timing on\n" + q + "\n")
        ms = re.findall(r"Time: ([\d.,]+) ms", out)
        return sum(float(m.replace(",", "")) for m in ms) / 1000

    def explicar(self, q, veces=5):
        tiempos, plan = [], ""
        for _ in range(veces):
            plan = self.sql("EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) " + q)
            tiempos.append(float(re.search(r"Execution Time: ([\d.]+) ms", plan).group(1)))
        return statistics.median(tiempos), plan

    def fin(self):
        docker("rm", "-f", self.n)


def mostrar_plan(pg, q, veces=5):
    p(f"$ EXPLAIN ANALYZE {q}")
    med, plan = pg.explicar(q, veces)
    for l in plan.splitlines():
        l2 = l.rstrip()
        if l2.startswith("Planning"):
            break
        if re.search(r"Scan|Filter|Index Cond|Rows Removed|Recheck|Heap Blocks|Heap Fetches|Sort|Limit|Buffers: shared", l2) \
                and "Planning" not in l2:
            p("  " + l2)
    p(f"  mediana de {veces}: {med:.3f} ms")
    return med


def main():
    cab = ["# SALIDA — «System design: índices» (cultura-devops, vídeo 348)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`"]
    pg = PG("postgres:17-alpine", "sd-indices")
    cab.append(f"- PostgreSQL {pg.version} (y 18 en la sección 5b) · shared_buffers 512MB · sin paralelismo · "
               f"{FILAS:,} filas".replace(",", "."))
    cab.append("- una sola máquina; los tiempos son de esta. Cada consulta: mediana de 5 ejecuciones.")
    cab.append("- los datos de Postgres van en tmpfs (memoria): la máquina renderiza vídeo a la vez y el disco "
               "metía ruido en las inserciones.")
    salida.append("\n```")
    try:
        t = pg.cronometrar(TABLA)
        p(f"[tabla pedidos: {FILAS:,} filas generadas en {t:.1f} s]".replace(",", "."))
        p("  " + pg.sql("SELECT 'tabla: ' || pg_size_pretty(pg_table_size('pedidos'))"))

        p("")
        p("== 1 · Buscar los pedidos de un cliente ==")
        q1 = "SELECT * FROM pedidos WHERE cliente_id = 4242"
        p("  filas que devuelve: " + pg.sql("SELECT count(*) FROM pedidos WHERE cliente_id = 4242"))
        sin = mostrar_plan(pg, q1)
        t = pg.cronometrar("CREATE INDEX pedidos_cliente ON pedidos (cliente_id);")
        p(f"$ CREATE INDEX pedidos_cliente ON pedidos (cliente_id);   -- {t:.1f} s")
        p("  " + pg.sql("SELECT 'índice: ' || pg_size_pretty(pg_relation_size('pedidos_cliente'))"))
        con = mostrar_plan(pg, q1)
        p(f"  → {sin / con:.0f} veces más rápido")

        p("")
        p("== 2 · Poca selectividad: el 80 % de los pedidos está 'entregado' ==")
        pg.sql("CREATE INDEX pedidos_estado ON pedidos (estado); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_estado ON pedidos (estado);")
        p("  " + pg.sql("SELECT string_agg(estado || ' ' || pct || ' %', ' · ' ORDER BY pct DESC) FROM "
                        "(SELECT estado, round(100.0 * count(*) / sum(count(*)) over (), 1) pct FROM pedidos GROUP BY estado) s"))
        mostrar_plan(pg, "SELECT sum(total) FROM pedidos WHERE estado = 'entregado'")
        mostrar_plan(pg, "SELECT sum(total) FROM pedidos WHERE estado = 'pendiente'")
        pg.sql("DROP INDEX pedidos_estado")

        p("")
        p("== 3 · Función sobre la columna ==")
        pg.sql("CREATE INDEX pedidos_email ON pedidos (email); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_email ON pedidos (email);")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE email = 'Cliente777777@correo.test'")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE lower(email) = 'cliente777777@correo.test'")
        pg.sql("CREATE INDEX pedidos_email_lower ON pedidos (lower(email)); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_email_lower ON pedidos (lower(email));")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE lower(email) = 'cliente777777@correo.test'")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE creado::date = date '2026-01-15'")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE creado >= '2026-01-15' AND creado < '2026-01-16'")

        p("")
        p("== 4 · LIKE con el comodín delante y detrás ==")
        p("  " + pg.sql("SELECT 'collation de la base: ' || datcollate FROM pg_database WHERE datname = 'postgres'"))
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE email LIKE 'Cliente77777%'")
        pg.sql("CREATE INDEX pedidos_email_patron ON pedidos (email text_pattern_ops); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_email_patron ON pedidos (email text_pattern_ops);")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE email LIKE 'Cliente77777%'")
        mostrar_plan(pg, "SELECT id FROM pedidos WHERE email LIKE '%77777@correo.test'")
        for i in ("pedidos_email", "pedidos_email_lower", "pedidos_email_patron"):
            pg.sql(f"DROP INDEX {i}")

        p("")
        p("== 5 · Índice compuesto (estado, creado) y una consulta solo por creado ==")
        pg.sql("CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado);")
        rango = "creado >= '2026-09-01' AND creado < '2026-09-02'"
        mostrar_plan(pg, f"SELECT id FROM pedidos WHERE estado = 'pendiente' AND {rango}")
        mostrar_plan(pg, f"SELECT id FROM pedidos WHERE {rango}")
        pg.sql("DROP INDEX pedidos_estado_creado; CREATE INDEX pedidos_creado_estado ON pedidos (creado, estado); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_creado_estado ON pedidos (creado, estado);   -- el orden al revés")
        mostrar_plan(pg, f"SELECT id FROM pedidos WHERE {rango}")
        pg.sql("DROP INDEX pedidos_creado_estado")
        pg.fin()

        p("")
        p("== 5b · Lo mismo en PostgreSQL 18 (skip scan) ==")
        pg = PG("postgres:18-alpine", "sd-indices18")
        p(f"  [PostgreSQL {pg.version}]")
        pg.cronometrar(TABLA)
        pg.sql("CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado); ANALYZE pedidos;")
        p("$ CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado);")
        mostrar_plan(pg, f"SELECT id FROM pedidos WHERE {rango}")
        pg.sql("DROP INDEX pedidos_estado_creado")
        pg.fin()
        pg = PG("postgres:17-alpine", "sd-indices")
        pg.cronometrar(TABLA)

        p("")
        p("== 6 · Lo que cuesta escribir: 200.000 inserciones con 0, 1, 3 y 6 índices ==")
        indices = ["cliente_id", "creado", "email", "estado", "total", "(cliente_id, creado)"]
        for n in (0, 1, 3, 6):
          ts = []
          for _ in range(5):
            pg.sql("DROP TABLE IF EXISTS escrituras; CREATE TABLE escrituras (LIKE pedidos INCLUDING DEFAULTS);")
            for i, col in enumerate(indices[:n]):
                pg.sql(f"CREATE INDEX esc_{i} ON escrituras ({col.strip('()')})")
            pg.sql("CHECKPOINT")
            ts.append(pg.cronometrar("INSERT INTO escrituras (cliente_id, estado, creado, email, total) "
                               "SELECT (random()*99999)::int + 1, 'pendiente', now() - random() * interval '1000 days', "
                               "'Nuevo' || g || '@correo.test', round((random()*500)::numeric, 2) "
                               "FROM generate_series(1, 200000) g;"))
          t = statistics.median(ts)
          tam = pg.sql("SELECT pg_size_pretty(pg_indexes_size('escrituras'))")
          p(f"  {n} índice{'s' if n != 1 else ''}: {t:.2f} s (mediana de 5) → {200000 / t:,.0f} filas/s · índices ocupan {tam}".replace(",", "."))
        salida.append("```")
    finally:
        docker("rm", "-f", "sd-indices", "sd-indices18")
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
