# -*- coding: utf-8 -*-
"""correr_extra.py — mediciones añadidas al vídeo 353 (no cambia SALIDA.md, escribe SALIDA-extra.md).

  1 sin partición: lo que cuesta el consenso. 1.000 escrituras seguidas en etcd (tres nodos) y en Redis
    (SET, y SET + WAIT 1), y lecturas lineales frente a serializables en etcd. Cliente Python dentro de la red.
  2 Redis WAIT con el primario aislado: el cliente sí puede enterarse
  3 etcd: se aísla a un seguidor, no al líder

    python correr_extra.py      -> SALIDA-extra.md
"""
import datetime
import time

import correr as K

CLIENTE = "sd-cap-cliente:1"
LAB = r'''
import base64, json, statistics, sys, time
import redis, requests

def b(s): return base64.b64encode(s.encode()).decode()

def medir(nombre, f, n=1000):
    for i in range(50): f(i)                       # calentar
    ts = []
    for i in range(n):
        t0 = time.perf_counter(); f(i); ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    print(f"  {nombre:<42} mediana {statistics.median(ts):6.3f} ms · p99 {ts[int(n * 0.99)]:7.3f} ms")

s = requests.Session()
reintentos = 0

def etcd(ruta, cuerpo):
    """503 = el clúster está cambiando de líder (pasa con la máquina cargada): se reintenta y se cuenta."""
    global reintentos
    while True:
        r = s.post(url + ruta, json=cuerpo)
        if r.status_code != 503:
            return r.raise_for_status()
        reintentos += 1

lider = sys.argv[1]
url = f"http://{lider}:2379/v3/kv"
medir("etcd put (consenso de 3 nodos)", lambda i: etcd("/put", {"key": b(f"k{i}"), "value": b("x")}))
medir("etcd get lineal (por defecto)", lambda i: etcd("/range", {"key": b("k1")}))
medir("etcd get serializable", lambda i: etcd("/range", {"key": b("k1"), "serializable": True}))
print(f"  (etcd contestó 503 «cambiando de líder» {reintentos} veces; se reintentó, y cuenta en el tiempo)")
r = redis.Redis(host="10.77.27.21")
medir("redis SET (asíncrono a la réplica)", lambda i: r.set(f"k{i}", "x"))
def set_wait(i):
    r.set(f"k{i}", "x")
    assert r.execute_command("WAIT", 1, 1000) == 1
medir("redis SET + WAIT 1 (espera a la réplica)", set_wait)
'''


def main():
    if not K.docker("images", "-q", CLIENTE)[1]:
        d = K.AQUI / "_cliente"
        d.mkdir(exist_ok=True)
        (d / "Dockerfile").write_text("FROM python:3.13-slim\nRUN pip install --no-cache-dir redis==6.4.0 requests==2.32.5\n",
                                      encoding="utf-8")
        K.docker("build", "-t", CLIENTE, str(d), check=True)
    (K.AQUI / "_lab_extra.py").write_text(LAB, encoding="utf-8")
    K.limpiar()
    K.docker("network", "create", "--subnet", K.SUBRED, K.RED, check=True)
    cab = ["# SALIDA-extra — «System design: el teorema CAP» (cultura-devops, vídeo 353)", "",
           "> Generado por `correr_extra.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           "- etcd 3.6.5 (tres nodos) · Redis 7.2.16 (primario y réplica) · cliente Python 3.13 (requests 2.32.5, "
           "redis 6.4.0) dentro de la red de Docker",
           "- una sola máquina, que además estaba renderizando vídeo: los tres nodos comparten disco y CPU. "
           "Los datos de etcd van en tmpfs (memoria) para que el disco ocupado no meta segundos de fsync."]
    K.salida.append("\n```")
    try:
        # etcd y Redis arriba, sin partición
        cluster = ",".join(f"{n}=http://{ip}:2380" for n, ip in K.NODOS.items())
        for n, ip in K.NODOS.items():
            K.docker("run", "-d", "--name", n, "--network", K.RED, "--ip", ip, "--tmpfs", "/tmp",
                     "--entrypoint", "etcd", K.ETCD,
                     "--name", n, "--data-dir", "/tmp/etcd", "--listen-peer-urls", "http://0.0.0.0:2380",
                     "--listen-client-urls", "http://0.0.0.0:2379", "--advertise-client-urls", f"http://{ip}:2379",
                     "--initial-advertise-peer-urls", f"http://{ip}:2380", "--initial-cluster", cluster,
                     "--initial-cluster-state", "new", check=True)
        K.docker("run", "-d", "--name", "r1", "--network", K.RED, "--ip", K.R1, K.REDIS, "redis-server", check=True)
        K.docker("run", "-d", "--name", "r2", "--network", K.RED, "--ip", K.R2, K.REDIS, "redis-server",
                 "--replicaof", K.R1, "6379", check=True)
        for _ in range(60):
            if K.ctl("etcd1", "put", "arranque", "ok")[0] == 0 and \
                    "master_link_status:up" in K.rcli("r2", "info", "replication")[1]:
                break
            time.sleep(1)
        _, st = K.ctl("etcd1", "endpoint", "status", "-w", "fields")
        lider_id = next(l.split(":")[1].strip() for l in st.splitlines() if l.startswith('"Leader"'))
        _, lista = K.ctl("etcd1", "member", "list")
        ids = {l.split(",")[2].strip(): format(int(l.split(",")[0], 16), "d") for l in lista.splitlines()}
        lider = next(n for n, i in ids.items() if i == lider_id)
        seguidor = next(n for n in K.NODOS if n != lider)

        K.p("== 1 · Sin partición: lo que cuesta el consenso (1.000 operaciones seguidas, una a una) ==")
        K.p(f"  [cliente contra el líder de etcd ({lider}) y contra el primario de Redis]")
        _, o = K.docker("run", "--rm", "--network", K.RED, "-v", f"{K.AQUI.as_posix()}:/lab", CLIENTE,
                        "python", "/lab/_lab_extra.py", NODOS_IP(lider))
        for l in o.splitlines():
            K.p(l)

        K.p("")
        K.p("== 2 · Redis WAIT con el primario aislado ==")
        K.docker("network", "disconnect", K.RED, "r1", check=True)
        K.p(f"$ docker network disconnect {K.RED} r1")
        for _ in range(60):   # aislado de verdad: r1 ya no llega a r2
            if K.docker("exec", "r1", "timeout", "2", "redis-cli", "-h", K.R2, "ping")[1] != "PONG":
                break
            time.sleep(0.5)
        _, o = K.docker("exec", "r1", "sh", "-c",
                        # el SET y el WAIT en la MISMA conexión: WAIT solo espera las escrituras de su conexión
                        "a=$(date +%s%N); printf 'SET pedido:1 pagado\nWAIT 1 2000\n' | redis-cli; b=$(date +%s%N); "
                        "echo \"(SET + WAIT tardaron $(( (b - a) / 1000000 )) ms)\"")
        K.p("$ r1> SET pedido:1 pagado ; WAIT 1 2000   # misma conexión: ¿cuántas réplicas lo tienen?")
        for l in o.splitlines():
            K.p("  " + l)
        K.docker("network", "connect", "--ip", K.R1, K.RED, "r1", check=True)

        K.p("")
        K.p(f"== 3 · etcd: se aísla a un seguidor ({seguidor}), no al líder ==")
        K.docker("network", "disconnect", K.RED, seguidor, check=True)
        K.p(f"$ docker network disconnect {K.RED} {seguidor}")
        _, st0 = K.ctl(lider, "endpoint", "status", "-w", "fields")
        term0 = next(l.split(":")[1].strip() for l in st0.splitlines() if l.startswith('"RaftTerm"'))
        time.sleep(1)
        t0 = time.time()
        K.mostrar(lider, "put", "saldo", "80", como="put saldo 80   # en la mayoría, el líder de siempre")
        K.p(f"  (contestó a los {time.time() - t0:.2f} s)")
        K.mostrar(seguidor, "put", "saldo", "90", como="put saldo 90   # en el seguidor aislado")
        _, st = K.ctl(lider, "endpoint", "status", "-w", "fields")
        sigue = next(l.split(":")[1].strip() for l in st.splitlines() if l.startswith('"Leader"'))
        _, rt = K.ctl(lider, "endpoint", "status", "-w", "fields")
        term = next(l.split(":")[1].strip() for l in rt.splitlines() if l.startswith('"RaftTerm"'))
        K.p(f"  líder antes: {lider} · después: {next(n for n, i in ids.items() if i == sigue)} · "
            f"término de Raft: {term0} → {term} " + ("(no hubo elección)" if term == term0 else "(HUBO elección)"))
        K.salida.append("```")
    finally:
        K.limpiar()
    (K.AQUI / "SALIDA-extra.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(K.salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA-extra.md")


def NODOS_IP(n):
    return K.NODOS[n]


if __name__ == "__main__":
    main()
