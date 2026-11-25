# -*- coding: utf-8 -*-
"""lab.py — las mediciones del vídeo de replicación. Corre DENTRO de la red de Docker (imagen
curso-sd-cliente:1); lo lanza correr.py, que es quien arranca, mata y promueve los Postgres.

    python lab.py retraso                       carga de escritura y muestras del retraso de la réplica
    python lab.py leer <n>                      escribe en el primario y lee al momento de la réplica
    python lab.py acks <segundos> <fichero>     escribe sin parar y apunta cada commit confirmado
    python lab.py perdidos <fichero> <host>     cuántos commits confirmados no están en <host>
    python lab.py latencias <n>                 latencia de commit: asíncrono, on y remote_apply
    python lab.py colgado <segundos>            un commit con la réplica síncrona caída (y cancelarlo)
"""
import statistics
import sys
import threading
import time

import psycopg

PRI = "host=sd-primario dbname=tienda user=postgres password=lab connect_timeout=3"
LOTE = 5000
TOPE = 1_500_000  # tope de filas por carga: el banco no debe llenar ningún disco
REP = "host=sd-replica1 dbname=tienda user=postgres password=lab connect_timeout=3"


def con(dsn, auto=True):
    for _ in range(120):
        try:
            return psycopg.connect(dsn, autocommit=auto)
        except psycopg.OperationalError:
            time.sleep(0.5)
    raise SystemExit(f"no conecta: {dsn.split()[0]}")


def lsn_diff(c, a, b):
    return c.execute("SELECT pg_wal_lsn_diff(%s, %s)", (a, b)).fetchone()[0]


def mb(n):
    return f"{n / 1024 / 1024:.1f} MB".replace(".", ",")


def carga(segundos, parar=None):
    """Inserciones en lotes de LOTE filas de ~200 bytes, hasta `segundos` o hasta `parar`, con un tope de filas."""
    c = con(PRI)
    fin = time.time() + segundos
    lotes = 0
    while time.time() < fin and not (parar and parar.is_set()):
        c.execute("INSERT INTO carga (relleno) SELECT repeat('x', 200) FROM generate_series(1, %s)", (LOTE,))
        lotes += 1
        if lotes * LOTE >= TOPE:
            break
    c.close()
    return lotes


def retraso():
    p = con(PRI)
    estado = p.execute("SELECT application_name, state, sync_state FROM pg_stat_replication").fetchall()
    for app, st, sync in estado:
        print(f"  réplica {app}: {st} · {sync}")
    muestras = []
    hilo = threading.Thread(target=lambda: muestras.append(("lotes", carga(5))))
    t0 = time.time()
    hilo.start()
    while hilo.is_alive():
        r = p.execute("""SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn),
                                extract(epoch FROM replay_lag) * 1000
                           FROM pg_stat_replication WHERE application_name = 'r1'""").fetchone()
        if r:
            muestras.append((time.time() - t0, r[0], r[1] or 0))
        time.sleep(0.2)
    lotes = next(m[1] for m in muestras if m[0] == "lotes")
    datos = [m for m in muestras if m[0] != "lotes"]
    pico_b = max(datos, key=lambda m: m[1])
    pico_ms = max(m[2] for m in datos)
    escrito = lotes * LOTE
    print(f"  5 s de carga en el primario: {escrito:,} filas".replace(",", "."))
    print(f"  retraso máximo de la réplica: {mb(pico_b[1])} de WAL sin aplicar (a los {pico_b[0]:.1f} s)")
    print(f"  replay_lag máximo: {pico_ms:,.0f} ms".replace(",", "."))
    t1 = time.time()
    while True:
        b = p.execute("""SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)
                           FROM pg_stat_replication WHERE application_name = 'r1'""").fetchone()[0]
        if b == 0:
            break
        time.sleep(0.1)
    print(f"  al parar la carga, la réplica tarda {time.time() - t1:.1f} s en ponerse al día".replace(".", ",", 1))


def leer(n):
    p, r = con(PRI), con(REP)
    for etiqueta, con_carga in (("sin carga", False), ("con carga de escritura", True)):
        parar = threading.Event()
        hilo = threading.Thread(target=carga, args=(600, parar)) if con_carga else None
        if hilo:
            hilo.start()
            time.sleep(1)
        faltan = []
        for _ in range(n):
            pid = p.execute("INSERT INTO pedidos (total) VALUES (100) RETURNING id").fetchone()[0]
            if r.execute("SELECT 1 FROM pedidos WHERE id = %s", (pid,)).fetchone() is None:
                faltan.append(pid)
        print(f"  {etiqueta}: {n} pedidos escritos en el primario y leídos al momento de la réplica -> "
              f"{len(faltan)} no estaban")
        # Control del banco: los mismos pedidos, un segundo después. Si aparecen, era retraso, no un fallo.
        time.sleep(1)
        siguen = r.execute("SELECT count(*) FROM pedidos WHERE id = ANY(%s)", (faltan,)).fetchone()[0]
        print(f"    control: 1 s después, de esos {len(faltan)} ya están {siguen}")
        parar.set()
        if hilo:
            hilo.join()
    # Lo correcto: esperar a que la réplica haya aplicado el LSN del commit (leer tus propias escrituras).
    parar = threading.Event()
    hilo = threading.Thread(target=carga, args=(600, parar))
    hilo.start()
    time.sleep(1)
    fallos, esperas = 0, []
    for _ in range(n):
        pid = p.execute("INSERT INTO pedidos (total) VALUES (100) RETURNING id").fetchone()[0]
        lsn = p.execute("SELECT pg_current_wal_insert_lsn()").fetchone()[0]
        t0 = time.time()
        while r.execute("SELECT pg_last_wal_replay_lsn() >= %s::pg_lsn", (lsn,)).fetchone()[0] is not True:
            time.sleep(0.002)
        esperas.append((time.time() - t0) * 1000)
        if r.execute("SELECT 1 FROM pedidos WHERE id = %s", (pid,)).fetchone() is None:
            fallos += 1
    parar.set()
    hilo.join()
    print(f"  esperando al LSN del commit antes de leer (con carga): {fallos} no estaban · "
          f"espera mediana {statistics.median(esperas):.0f} ms, máxima {max(esperas):.0f} ms")


def acks(segundos, fichero):
    """Escribe pedidos uno a uno y apunta el id de cada commit que el primario confirmó."""
    p = con(PRI)
    hechos = 0
    fin = time.time() + float(segundos)
    with open(fichero, "w") as f:
        while time.time() < fin:
            try:
                pid = p.execute("INSERT INTO pedidos (total) VALUES (100) RETURNING id").fetchone()[0]
            except psycopg.Error:
                break
            f.write(f"{pid}\n")
            f.flush()
            hechos += 1
    print(f"  commits confirmados por el primario antes de caer: {hechos}")


def perdidos(fichero, host):
    ids = [int(l) for l in open(fichero) if l.strip()]
    c = con(f"host={host} dbname=tienda user=postgres password=lab connect_timeout=3")
    hay = {r[0] for r in c.execute("SELECT id FROM pedidos WHERE id = ANY(%s)", (ids,)).fetchall()}
    faltan = [i for i in ids if i not in hay]
    print(f"  en la réplica promovida: {len(hay)} de {len(ids)} · confirmados y PERDIDOS: {len(faltan)}")


def latencias(n):
    p = con(PRI)
    for modo in ("off", "local", "on", "remote_apply"):
        if modo == "off":
            continue
        p.execute(f"SET synchronous_commit = {modo}")
        t = []
        for _ in range(n):
            t0 = time.perf_counter()
            p.execute("INSERT INTO pedidos (total) VALUES (100)")
            t.append((time.perf_counter() - t0) * 1000)
        t.sort()
        nombre = {"local": "asíncrona (local)", "on": "síncrona (on)", "remote_apply": "síncrona (remote_apply)"}[modo]
        print(f"  {nombre:<26} mediana {statistics.median(t):.2f} ms · p99 {t[int(n * 0.99) - 1]:.2f} ms"
              .replace(".", ","))


def colgado(segundos):
    """Un commit con la réplica síncrona caída. statement_timeout NO lo corta: Postgres lo desactiva
    antes del commit, y la espera a la réplica es parte del commit. Se espera <segundos>, y si sigue
    colgado se cancela desde otra conexión (pg_cancel_backend), como haría un operador."""
    p = con(PRI)
    avisos = []
    p.add_notice_handler(lambda d: avisos.extend(x for x in (d.message_primary, d.message_detail) if x))
    antes = p.execute("SELECT count(*) FROM pedidos").fetchone()[0]
    p.execute("SET statement_timeout = '2s'")
    pid = p.info.backend_pid
    res = {}

    def insertar():
        t0 = time.time()
        try:
            p.execute("INSERT INTO pedidos (total) VALUES (100) RETURNING id")
            res["ok"] = time.time() - t0
        except psycopg.Error as e:
            res["error"] = (time.time() - t0, type(e).__name__)

    h = threading.Thread(target=insertar)
    h.start()
    h.join(timeout=float(segundos))
    if h.is_alive():
        print(f"  a los {segundos} s el INSERT sigue esperando (statement_timeout = 2 s no lo corta)")
        con(PRI).execute("SELECT pg_cancel_backend(%s)", (pid,))
        print("  $ SELECT pg_cancel_backend(pid)   -- desde otra conexión")
        h.join(timeout=10)
    if "ok" in res:
        print(f"  el INSERT volvió en {res['ok']:.1f} s".replace(".", ",", 1))
    if "error" in res:
        print(f"  el INSERT terminó con {res['error'][1]} a los {res['error'][0]:.1f} s".replace(".", ",", 1))
    for a in avisos:
        print(f"  aviso de Postgres: {a}")
    n = con(PRI).execute("SELECT count(*) FROM pedidos").fetchone()[0]
    print(f"  ¿quedó escrito en el primario?: {n > antes} (pedidos antes: {antes}, ahora: {n})")


if __name__ == "__main__":
    orden, args = sys.argv[1], sys.argv[2:]
    {"retraso": lambda: retraso(), "leer": lambda: leer(int(args[0])),
     "acks": lambda: acks(args[0], args[1]), "perdidos": lambda: perdidos(args[0], args[1]),
     "latencias": lambda: latencias(int(args[0])), "colgado": lambda: colgado(int(args[0]))}[orden]()
