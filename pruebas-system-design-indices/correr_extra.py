# -*- coding: utf-8 -*-
"""correr_extra.py — mediciones añadidas al vídeo 348 (no cambia SALIDA.md, escribe SALIDA-extra.md).

Misma tabla y mismo Postgres que correr.py (17, datos en tmpfs, mediana de 5):

  1 la fecha convertida (creado::date) frente al rango, con un índice sobre creado
  2 ORDER BY creado DESC LIMIT 10, sin y con índice
  3 índice parcial: solo los pendientes
  4 índice que cubre la consulta (INCLUDE): index-only scan

    python correr_extra.py      -> SALIDA-extra.md
"""
import datetime

import correr as K


def main():
    cab = ["# SALIDA-extra — «System design: índices» (cultura-devops, vídeo 348)", "",
           "> Generado por `correr_extra.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`"]
    pg = K.PG("postgres:17-alpine", "sd-indices")
    cab += [f"- PostgreSQL {pg.version} · la misma tabla de correr.py (2.000.000 de pedidos) · datos en tmpfs",
            "- una sola máquina, renderizando vídeo a la vez. Cada consulta: mediana de 5 ejecuciones."]
    K.salida.append("\n```")
    try:
        pg.cronometrar(K.TABLA)
        K.p("== 1 · La fecha convertida frente al rango, con un índice sobre creado ==")
        pg.sql("CREATE INDEX pedidos_creado ON pedidos (creado); ANALYZE pedidos;")
        K.p("$ CREATE INDEX pedidos_creado ON pedidos (creado);")
        K.mostrar_plan(pg, "SELECT id FROM pedidos WHERE creado::date = date '2026-01-15'")
        K.mostrar_plan(pg, "SELECT id FROM pedidos WHERE creado >= '2026-01-15' AND creado < '2026-01-16'")

        K.p("")
        K.p("== 2 · Los 10 pedidos más recientes ==")
        K.mostrar_plan(pg, "SELECT id, creado FROM pedidos ORDER BY creado DESC LIMIT 10")
        pg.sql("DROP INDEX pedidos_creado; ANALYZE pedidos;")
        K.p("$ DROP INDEX pedidos_creado;")
        K.mostrar_plan(pg, "SELECT id, creado FROM pedidos ORDER BY creado DESC LIMIT 10")

        K.p("")
        K.p("== 3 · Índice parcial: solo los pendientes (5 %) ==")
        pg.sql("CREATE INDEX pedidos_creado_todos ON pedidos (creado); "
               "CREATE INDEX pedidos_pendientes ON pedidos (creado) WHERE estado = 'pendiente'; ANALYZE pedidos;")
        K.p("$ CREATE INDEX pedidos_creado_todos ON pedidos (creado);")
        K.p("$ CREATE INDEX pedidos_pendientes ON pedidos (creado) WHERE estado = 'pendiente';")
        K.p("  " + pg.sql("SELECT string_agg(relname || ': ' || pg_size_pretty(pg_relation_size(oid)), ' · ') "
                          "FROM pg_class WHERE relname IN ('pedidos_creado_todos', 'pedidos_pendientes')"))
        K.mostrar_plan(pg, "SELECT id FROM pedidos WHERE estado = 'pendiente' ORDER BY creado LIMIT 20")
        pg.sql("DROP INDEX pedidos_creado_todos, pedidos_pendientes")

        K.p("")
        K.p("== 4 · Índice que cubre la consulta: el total de los pedidos de un cliente ==")
        pg.sql("CREATE INDEX pedidos_cliente ON pedidos (cliente_id); ANALYZE pedidos;")
        K.p("$ CREATE INDEX pedidos_cliente ON pedidos (cliente_id);")
        K.mostrar_plan(pg, "SELECT sum(total) FROM pedidos WHERE cliente_id BETWEEN 4000 AND 4999")
        pg.sql("DROP INDEX pedidos_cliente; CREATE INDEX pedidos_cliente_total ON pedidos (cliente_id) INCLUDE (total);")
        pg.sql("VACUUM ANALYZE pedidos")
        K.p("$ CREATE INDEX pedidos_cliente_total ON pedidos (cliente_id) INCLUDE (total);")
        K.mostrar_plan(pg, "SELECT sum(total) FROM pedidos WHERE cliente_id BETWEEN 4000 AND 4999")
        K.salida.append("```")
    finally:
        pg.fin()
    (K.AQUI / "SALIDA-extra.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(K.salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA-extra.md")


if __name__ == "__main__":
    main()
