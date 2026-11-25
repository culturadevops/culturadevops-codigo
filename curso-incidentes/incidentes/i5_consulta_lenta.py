# -*- coding: utf-8 -*-
"""Incidente 5 · La consulta lenta que solo lo es en producción.

El historial de pedidos de un cliente: rapidísimo en pruebas, con mil filas. En producción hay
millones, y la consulta lee la tabla entera cada vez porque no hay índice. Nadie cambió el
código: cambió el tamaño de los datos. Y en pruebas no se puede ver.
"""
import time

from comun import TIENDA, Cronologia, Trafico, docker, esperar_alerta, postmortem, prom1, titulo


def psql(sql):
    return docker("exec", "-T", "db", "psql", "-U", "admin", "-d", "tienda", "-qAt", "-c", sql)


def media_ms():
    v = prom1('rate(tienda_latencia_suma_segundos{ruta="/historial"}[30s])'
              ' / rate(tienda_latencia_cuenta{ruta="/historial"}[30s])')
    return f"{v * 1000:.0f} ms" if v is not None else "-"


def sembrar(n):
    psql("DROP TABLE IF EXISTS pedidos; CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
         "CREATE TABLE pedidos (id bigserial PRIMARY KEY, cliente int NOT NULL, total numeric(10,2) NOT NULL,"
         " creado timestamptz NOT NULL DEFAULT now());"
         f"INSERT INTO pedidos (cliente, total, creado) SELECT (random()*50000)::int, random()*200,"
         f" now() - random() * interval '365 days' FROM generate_series(1, {n}); ANALYZE pedidos;")


docker("up", "-d", "tienda")
cron = Cronologia()
inicio = time.time()

titulo("5.1 · En pruebas: mil pedidos")
sembrar(1000)
with Trafico(f"{TIENDA}/historial?cliente=42", hilos=4, pausa=0.1, timeout=10) as tr:
    time.sleep(40)
    print(f"  {psql('SELECT count(*) FROM pedidos').strip()} pedidos · media del historial: {media_ms()} · {tr.resumen()}")

titulo("5.2 · En producción: tres millones (y un Postgres con media CPU)")
sembrar(3_000_000)
psql("SELECT pg_stat_statements_reset()")
cron.marca(f"producción: {psql('SELECT count(*) FROM pedidos').strip()} pedidos, el mismo código")
with Trafico(f"{TIENDA}/historial?cliente=42", hilos=4, pausa=0.1, timeout=10) as tr:
    t = esperar_alerta("HistorialLento", inicio)
    cron.marca("ALERTA HistorialLento: «el historial tarda de media más de 300 ms»", t)
    print(f"  media del historial: {media_ms()} · {tr.resumen()}")

    titulo("5.3 · Diagnóstico: ¿qué consulta? pg_stat_statements")
    print(psql("SELECT '  ' || calls || ' llamadas · media ' || round(mean_exec_time) || ' ms · ' || "
               "left(regexp_replace(query, '\\s+', ' ', 'g'), 70) FROM pg_stat_statements "
               "WHERE query ILIKE '%WHERE cliente%' ORDER BY mean_exec_time DESC LIMIT 1").rstrip())
    cron.marca("la consulta más lenta: el historial")

    titulo("5.4 · Diagnóstico: ¿por qué? EXPLAIN ANALYZE")
    for l in psql("EXPLAIN (ANALYZE, COSTS OFF) SELECT id, total FROM pedidos WHERE cliente = 42 "
                  "ORDER BY creado DESC LIMIT 10").splitlines():
        print("  " + l)
    cron.marca("causa: lee la tabla entera (no hay índice por cliente)")

    titulo("5.5 · Mitigar: un índice, creado sin bloquear la tabla")
    t0 = time.time()
    psql("CREATE INDEX CONCURRENTLY pedidos_cliente_creado ON pedidos (cliente, creado DESC)")
    cron.marca(f"MITIGADO: índice creado con CONCURRENTLY en {time.time() - t0:.1f} s, sin cortar el tráfico")
    for l in psql("EXPLAIN (ANALYZE, COSTS OFF) SELECT id, total FROM pedidos WHERE cliente = 42 "
                  "ORDER BY creado DESC LIMIT 10").splitlines():
        print("  " + l)
    t = esperar_alerta("HistorialLento", inicio, estado="resolved")
    cron.marca("la alerta se resuelve", t)
    time.sleep(30)
    print(f"  media del historial: {media_ms()} · {tr.resumen()}")

titulo("5.6 · El postmortem")
postmortem(5, "La consulta lenta que solo lo es en producción", cron,
           resumen="El historial de pedidos pasó de unos milisegundos en pruebas a cientos en producción, "
                   "con el mismo código.",
           causa="La consulta filtra por cliente y no había índice: con mil filas, leer la tabla entera es "
                 "instantáneo; con tres millones, no. El entorno de pruebas no podía enseñarlo.",
           bien=["La alerta de latencia por ruta señaló el historial, no «la web va lenta».",
                 "pg_stat_statements y EXPLAIN dieron la causa en dos consultas.",
                 "CREATE INDEX CONCURRENTLY lo arregló sin bloquear la tabla."],
           mal=["Las pruebas usan mil filas: ninguna prueba podía ver esto.",
                "Nadie revisa el plan de las consultas nuevas."],
           acciones=["Datos de pruebas con el volumen de producción (anonimizados) para las consultas nuevas.",
                     "EXPLAIN de cada consulta nueva en la revisión de código.",
                     "Índices siempre con CONCURRENTLY en una tabla con tráfico."])
