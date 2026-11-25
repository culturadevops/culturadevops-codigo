# -*- coding: utf-8 -*-
"""Segunda parte del banco del vídeo 351 (replicación). Escribe SALIDA-extra.md.

Aparte de correr.py para no rehacer sus números. Mismo laboratorio:
  8  escribir en la réplica (es de solo lectura)
  9  el slot de replicación con la réplica caída: el primario guarda el WAL que nadie recoge

    python correr_extra.py
"""
import datetime
import time

import correr as C

C.salida = []
p = C.p


def sql(contenedor, q, usuario=True):
    pre = ["exec", contenedor] + (["gosu", "postgres"] if contenedor != "sd-primario" else [])
    return C.docker(*pre, "psql", "-U", "postgres", "-d", "tienda", "-tAc", q)[1]


def main():
    try:
        C.salida.append("```")
        C.montar()
        p("== 8 · Escribir en la réplica ==")
        p("$ psql -h sd-replica1 -c \"INSERT INTO pedidos (total) VALUES (100)\"")
        p("  " + sql("sd-replica1", "INSERT INTO pedidos (total) VALUES (100)").splitlines()[0])
        p("")
        p("== 9 · La réplica se cae y el primario sigue escribiendo: el slot guarda el WAL ==")
        p("  slot: " + sql("sd-primario", "SELECT slot_name || ' · ' || slot_type || ' · activo: ' || active FROM pg_replication_slots"))
        p("  pg_wal antes: " + C.docker("exec", "sd-primario", "du", "-sh", "/var/lib/postgresql/data/pg_wal")[1].split()[0])
        C.docker("stop", "sd-replica1")
        p("$ docker stop sd-replica1   y 10 s de carga de escritura en el primario")
        C.docker("run", "--rm", "--network", C.RED, "-v", f"{C.AQUI.as_posix()}:/lab", C.CLIENTE,
                 "python", "-c", "import lab; lab.carga(10)")
        time.sleep(2)
        p("  slot: " + sql("sd-primario", "SELECT slot_name || ' · activo: ' || active || ' · WAL retenido: ' || "
                           "pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) FROM pg_replication_slots"))
        p("  pg_wal después: " + C.docker("exec", "sd-primario", "du", "-sh", "/var/lib/postgresql/data/pg_wal")[1].split()[0])
        p("  max_slot_wal_keep_size: " + sql("sd-primario", "SHOW max_slot_wal_keep_size"))
        C.salida.append("```")
    finally:
        C.limpiar()
    cab = ["# SALIDA — replicación, segunda parte (cultura-devops, vídeo 351)", "",
           "> Generado por `correr_extra.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}` · mismo laboratorio que SALIDA.md"]
    (C.AQUI / "SALIDA-extra.md").write_bytes(("\n".join(cab) + "\n\n" + "\n".join(C.salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA-extra.md")


if __name__ == "__main__":
    main()
