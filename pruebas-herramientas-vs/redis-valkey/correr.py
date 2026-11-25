# -*- coding: utf-8 -*-
"""correr.py — «¿Redis o Valkey? Lo medí» (cultura-devops 840, pedido del dueño 2026-11-05).

    python correr.py              → SALIDA.md
    python correr.py --preparar   → solo baja las imágenes (sin candado, sin medir)

Montaje (igual para los dos):
  · imágenes OFICIALES fijadas (redis:8.8.4, valkey/valkey:9.1.3), 2 CPU y 1 GiB;
  · config de caché de producción razonable e IGUAL: maxmemory 768mb + allkeys-lru, el resto de fábrica (instantáneas RDB de
    fábrica, sin AOF); y una segunda variante de cada uno con io-threads 2 (hilos de E/S, la novedad de Valkey 8 que Redis 8
    también tiene);
  · la carga: memtier_benchmark 2.5.2 (imagen oficial redislabs/memtier_benchmark) desde OTRO contenedor de la misma red, 6 CPU;
  · 1.000.000 de claves de 100 bytes cargadas por memtier; antes de medir se comprueba en los dos el mismo número de claves y
    los mismos valores (sha256 de tres claves). Si no, exit 1.
"""
import re
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun as K  # noqa: E402
from comun import w, sh, ok, num  # noqa: E402

MT = "redislabs/memtier_benchmark:2.5.2"
VOL = "hvs-kv"
CLAVES, TAM = 1_000_000, 100
SEG, SEG_CAL, REPES = 30, 5, 5
T, CX = 4, 50   # memtier: 4 hilos × 50 conexiones = 200 conexiones
S = {
    "redis": dict(nombre="Redis", img="redis:8.8.4", srv="redis-server", cli="redis-cli"),
    "valkey": dict(nombre="Valkey", img="valkey/valkey:9.1.3", srv="valkey-server", cli="valkey-cli"),
}
VARIANTES = [("redis", 1), ("redis", 2), ("valkey", 1), ("valkey", 2)]


def nv(k, io):
    return f"{S[k]['nombre']}" + (" · io-threads 2" if io == 2 else "")


def arrancar(k, io=1, volumen=False):
    K.rm("kv")
    args = ["docker", "run", "-d", "--rm", "--name", "kv", "--network", K.RED, "--cpus", K.CPUS, "--memory", K.MEM,
            "-p", "9401:6379"]
    if volumen:
        args += ["-v", f"{VOL}:/data"]
    t0 = time.perf_counter()
    ok(args + [S[k]["img"], S[k]["srv"], "--maxmemory", "768mb", "--maxmemory-policy", "allkeys-lru", "--io-threads", str(io)])
    return t0


def pong(t0, limite=120):
    """Hasta que PING devuelve +PONG (mientras carga el RDB responde -LOADING)."""
    while True:
        try:
            with socket.create_connection(("127.0.0.1", 9401), timeout=1) as s:
                s.sendall(b"PING\r\n")
                if s.recv(64).startswith(b"+PONG"):
                    return (time.perf_counter() - t0) * 1000
        except OSError:
            pass
        if time.perf_counter() - t0 > limite:
            raise SystemExit("⛔ no respondió PONG")
        time.sleep(0.005)


def cli(k, *args):
    return ok(["docker", "exec", "kv", S[k]["cli"]] + list(args)).stdout.strip()


def info(k, campo):
    return int(re.search(rf"^{campo}:(\d+)", cli(k, "INFO", "memory"), re.M).group(1))


def memtier(extra, seg=SEG):
    r = sh(["docker", "run", "--rm", "--network", K.RED, "--cpus", "6", MT, "-s", "kv", "-p", "6379", "--protocol=redis",
            "--hide-histogram", f"--data-size={TAM}"] + extra + ([f"--test-time={seg}"] if seg else []))
    t = r.stdout
    if r.returncode != 0 or "Totals" not in t:
        raise SystemExit(f"⛔ memtier falló:\n{t[-2000:]}\n{r.stderr[-2000:]}")
    cab = re.search(r"^Type\s+(.+)$", t, re.M).group(1)
    cols = re.split(r"\s{2,}", cab.strip())
    vals = re.search(r"^Totals\s+(.+)$", t, re.M).group(1).split()
    d = dict(zip(cols, vals))
    return dict(ops=float(d["Ops/sec"]), p50=float(d["p50 Latency"]), p99=float(d["p99 Latency"]),
                p999=float(d["p99.9 Latency"]))


def cargar_claves():
    t0 = time.perf_counter()
    memtier(["--ratio=1:0", "--requests=allkeys", "--key-pattern=P:P", "--key-minimum=1", f"--key-maximum={CLAVES}",
             "-t", "2", "-c", "10"], seg=None)
    return time.perf_counter() - t0


def mezcla(pipeline=1, rate=None):
    x = ["--ratio=1:10", "--key-pattern=R:R", "--key-minimum=1", f"--key-maximum={CLAVES}", "-t", str(T), "-c", str(CX),
         f"--pipeline={pipeline}"]
    if rate:
        x.append(f"--rate-limiting={rate}")
    return x


def main():
    K.red()
    for i in [MT] + [S[k]["img"] for k in S]:
        if sh(["docker", "image", "inspect", i]).returncode != 0:
            ok(["docker", "pull", "-q", i])
    if "--preparar" in sys.argv:
        print("[ok] imágenes listas")
        return
    K.OUT.clear()
    res = {}
    with K.candado("redis-valkey"):
        w("# SALIDA — ¿Redis o Valkey? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)\n")
        w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}, bajo el candado _logs/banco.lock. Regenerable con `python correr.py`. "
          "⛔ Ninguna cifra de blog: todo salió de aquí.\n")
        for k in S:
            v = ok(["docker", "run", "--rm", S[k]["img"], S[k]["srv"], "--version"]).stdout.strip()
            w(f"- {S[k]['nombre']}: `{v}` — imagen oficial `{S[k]['img']}`")
        v = sh(["docker", "run", "--rm", MT, "--version"])
        w(f"- Carga: `{(v.stdout + v.stderr).strip().splitlines()[0]}` (`{MT}`) desde otro contenedor con 6 CPU: "
          f"{T} hilos × {CX} conexiones = {T * CX} conexiones.")
        w(f"- Docker `{sh(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip()}` (Docker Desktop, Windows 11, 24 hilos); "
          f"servidor con {K.CPUS} CPU y {K.MEM}. Config igual en los dos: `--maxmemory 768mb --maxmemory-policy allkeys-lru "
          "--io-threads 1|2`; lo demás de fábrica (instantáneas RDB, sin AOF).")
        w(f"- Datos: {num(CLAVES, 0)} claves (memtier-1 … memtier-{CLAVES}) de {TAM} bytes, escritas por memtier.\n")

        w("## 0 · ¿Llegaron los dos al mismo estado? (antes de medir)\n")
        huellas = {}
        for k in S:
            arrancar(k)
            pong(time.perf_counter())
            cargar_claves()
            n = int(cli(k, "DBSIZE"))
            h = ok(["docker", "exec", "kv", "sh", "-c",
                    f"for c in memtier-1 memtier-{CLAVES // 2} memtier-{CLAVES}; do {S[k]['cli']} --raw GET $c | sha256sum; done"]).stdout.split()
            huellas[k] = (n, h[0::2])
            w(f"- {S[k]['nombre']}: DBSIZE {n}, sha256 de memtier-1 / -{CLAVES // 2} / -{CLAVES}: "
              + " / ".join(x[:12] + "…" for x in h[0::2]))
            K.rm("kv")
        if not (huellas["redis"] == huellas["valkey"] and huellas["redis"][0] == CLAVES):
            K.guardar(AQUI / "SALIDA-NO-COMPARABLE.md")
            raise SystemExit("no llegaron al mismo estado: no se compara")
        w("- → igual en los dos.\n")

        w("## 1 · Lo que despliegas\n")
        w("| servidor | imagen | tamaño en disco |")
        w("|---|---|---|")
        for k in S:
            w(f"| {S[k]['nombre']} | `{S[k]['img']}` | {num(K.tam_imagen(S[k]['img']))} MiB |")
        w()

        w(f"## 2 · Arranque, memoria y {num(CLAVES, 0)} claves\n")
        w(f"Arranque en vacío = `docker run` → primer +PONG (mediana de {REPES}). Recarga = reinicio con el RDB del millón de claves "
          "en un volumen → primer +PONG (mientras carga responde -LOADING; mediana de 3). used_memory = lo que dice el propio servidor "
          "(INFO memory); contenedor = docker stats.\n")
        w("| servidor | arranque en vacío | reposo (contenedor) | cargar 1 M claves | used_memory con 1 M | por clave | contenedor con 1 M | RDB en disco | recarga del RDB |")
        w("|---|---|---|---|---|---|---|---|---|")
        for k in S:
            ts, mems = [], []
            for _ in range(REPES):
                t0 = arrancar(k)
                ts.append(pong(t0))
                time.sleep(2)
                mems.append(K.stats("kv")[0])
            sh(["docker", "volume", "rm", "-f", VOL])
            arrancar(k, volumen=True)
            pong(time.perf_counter())
            vacio = info(k, "used_memory")
            carga = cargar_claves()
            lleno = info(k, "used_memory")
            time.sleep(2)
            cont = K.stats("kv")[0]
            cli(k, "SAVE")
            rdb = int(ok(["docker", "exec", "kv", "sh", "-c", "stat -c %s /data/dump.rdb"]).stdout.strip()) / 1048576
            recargas = []
            for _ in range(3):
                ok(["docker", "stop", "kv"])
                while sh(["docker", "inspect", "kv"]).returncode == 0:
                    time.sleep(0.1)
                t0 = arrancar(k, volumen=True)
                recargas.append(pong(t0))
            assert int(cli(k, "DBSIZE")) == CLAVES, "el RDB no trajo el millón de claves"
            K.rm("kv")
            sh(["docker", "volume", "rm", "-f", VOL])
            w(f"| {S[k]['nombre']} | {num(K.mediana(ts), 0)} ms | {num(K.mediana(mems))} MiB | {num(carga)} s | "
              f"{num(lleno / 1048576)} MiB | {num((lleno - vacio) / CLAVES, 0)} bytes | {num(cont)} MiB | {num(rdb)} MiB | "
              f"{num(K.mediana(recargas), 0)} ms |")
        w()

        for titulo, pipe in (("3 · A tope: 1 SET por cada 10 GET, sin pipeline", 1), ("4 · A tope con pipeline de 16 (1:10)", 16)):
            w(f"## {titulo} — memtier {T}×{CX} conexiones, {SEG} s tras {SEG_CAL} s de calentamiento, claves al azar entre el millón\n")
            w("| servidor | operaciones/s | p50 | p99 | p99,9 | memoria máx. | CPU media |")
            w("|---|---|---|---|---|---|---|")
            for k, io in VARIANTES:
                arrancar(k, io)
                pong(time.perf_counter())
                cargar_claves()
                memtier(mezcla(pipe), seg=SEG_CAL)
                with K.Muestreo("kv") as m:
                    r = memtier(mezcla(pipe))
                r.update(mem=m.mem_max, cpu=m.cpu_media)
                res[(k, io, pipe)] = r
                K.rm("kv")
                w(f"| {nv(k, io)} | {num(r['ops'], 0)} | {num(r['p50'], 3)} ms | {num(r['p99'], 3)} ms | {num(r['p999'], 3)} ms | "
                  f"{num(r['mem'])} MiB | {num(r['cpu'], 0)} % |")
            w()

        tope = min(res[(k, io, 1)]["ops"] for k, io in VARIANTES)
        por_cx = max(1, int(tope / 2 / (T * CX)))
        w(f"## 5 · El mismo tráfico para los dos: {num(por_cx * T * CX, 0)} operaciones/s fijas (la mitad del más lento a tope), 1:10, sin pipeline\n")
        w("| servidor | operaciones/s servidas | p50 | p99 | p99,9 | CPU media |")
        w("|---|---|---|---|---|---|")
        for k, io in VARIANTES:
            arrancar(k, io)
            pong(time.perf_counter())
            cargar_claves()
            memtier(mezcla(1, por_cx), seg=SEG_CAL)
            with K.Muestreo("kv") as m:
                r = memtier(mezcla(1, por_cx), seg=20)
            K.rm("kv")
            w(f"| {nv(k, io)} | {num(r['ops'], 0)} | {num(r['p50'], 3)} ms | {num(r['p99'], 3)} ms | {num(r['p999'], 3)} ms | "
              f"{num(m.cpu_media, 0)} % |")
        w()
        sh(["docker", "volume", "rm", "-f", VOL])
    K.guardar(AQUI / "SALIDA.md")


if __name__ == "__main__":
    main()
