# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: el teorema CAP con una red partida de verdad» (cultura-devops, 353).

La partición es real: `docker network disconnect` deja a un contenedor sin red. Los clientes de cada lado
escriben con `docker exec`, que llega al contenedor aunque esté aislado: así se puede escribir en la
minoría y en la mayoría a la vez.

  1 etcd 3.6.5, tres nodos: se aísla al líder · lado mayoritario y lado minoritario · lectura lineal y serializable
  2 Redis 7.2 con réplica y tres sentinels: se aísla al primario · escrituras aceptadas y perdidas
  3 Redis con min-replicas-to-write 1: cuántas acepta antes de empezar a rechazar

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-cap", "10.77.27.0/24"
ETCD, REDIS = "gcr.io/etcd-development/etcd:v3.6.5", "redis:7.2"
salida = []
NODOS = {"etcd1": "10.77.27.11", "etcd2": "10.77.27.12", "etcd3": "10.77.27.13"}
R1, R2 = "10.77.27.21", "10.77.27.22"
SENT = {"s1": "10.77.27.31", "s2": "10.77.27.32", "s3": "10.77.27.33"}


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return r.returncode, (r.stdout + r.stderr).strip()


def ctl(nodo, *a, timeout="3s"):
    return docker("exec", nodo, "etcdctl", "--endpoints=127.0.0.1:2379", f"--command-timeout={timeout}", *a)


def mostrar(nodo, *a, como=None):
    c, o = ctl(nodo, *a)
    p(f"$ {nodo}> etcdctl {como or ' '.join(a)}")
    for l in o.splitlines()[-2:]:
        p("  " + l)
    return c


def limpiar():
    docker("rm", "-f", *NODOS, "r1", "r2", *SENT)
    docker("network", "rm", RED)


def etcd():
    cluster = ",".join(f"{n}=http://{ip}:2380" for n, ip in NODOS.items())
    for n, ip in NODOS.items():
        docker("run", "-d", "--name", n, "--network", RED, "--ip", ip, "--entrypoint", "etcd", ETCD,
               "--name", n, "--data-dir", "/tmp/etcd", "--listen-peer-urls", "http://0.0.0.0:2380",
               "--listen-client-urls", "http://0.0.0.0:2379", "--advertise-client-urls", f"http://{ip}:2379",
               "--initial-advertise-peer-urls", f"http://{ip}:2380", "--initial-cluster", cluster,
               "--initial-cluster-state", "new", check=True)
    for _ in range(60):
        if ctl("etcd1", "endpoint", "health")[0] == 0 and ctl("etcd1", "put", "arranque", "ok")[0] == 0:
            break
        time.sleep(1)
    _, st = ctl("etcd1", "endpoint", "status", "--cluster", "-w", "fields")
    lider_id = next(l.split(":")[1].strip() for l in st.splitlines() if l.startswith('"Leader"'))
    _, lista = ctl("etcd1", "member", "list")
    ids = {l.split(",")[2].strip(): format(int(l.split(",")[0], 16), "d") for l in lista.splitlines()}
    lider = next(n for n, i in ids.items() if i == lider_id)
    resto = [n for n in NODOS if n != lider]
    p(f"[etcd {ETCD.split(':')[1]}: tres nodos · líder: {lider}]")
    mostrar(lider, "put", "saldo", "100")

    p("")
    p(f"== 1 · Se corta la red del líder ({lider}) ==")
    docker("network", "disconnect", RED, lider, check=True)
    p(f"$ docker network disconnect {RED} {lider}")
    time.sleep(1)
    t0 = time.time()
    mostrar(lider, "put", "saldo", "50", como="put saldo 50   # en la minoría (1 de 3)")
    p(f"  (contestó a los {time.time() - t0:.1f} s)")
    for _ in range(30):
        if ctl(resto[0], "put", "saldo", "70")[0] == 0:
            break
        time.sleep(0.5)
    mostrar(resto[0], "put", "saldo", "70", como="put saldo 70   # en la mayoría (2 de 3)")
    mostrar(resto[1], "get", "saldo", "--print-value-only", como="get saldo   # mayoría")
    mostrar(lider, "get", "saldo", "--print-value-only", como="get saldo   # minoría, lectura lineal (por defecto)")
    mostrar(lider, "get", "saldo", "--print-value-only", "--consistency=s",
            como="get saldo --consistency=s   # minoría, lectura serializable")
    _, st = ctl(resto[0], "endpoint", "status", "-w", "fields")
    nuevo = next(l.split(":")[1].strip() for l in st.splitlines() if l.startswith('"Leader"'))
    p(f"  nuevo líder en la mayoría: {next(n for n, i in ids.items() if i == nuevo)}")

    p("")
    p("== 2 · Vuelve la red ==")
    docker("network", "connect", "--ip", NODOS[lider], RED, lider, check=True)
    p(f"$ docker network connect {RED} {lider}")
    for _ in range(30):
        c, o = ctl(lider, "get", "saldo", "--print-value-only")
        if c == 0 and o.strip() == "70":
            break
        time.sleep(0.5)
    mostrar(lider, "get", "saldo", "--print-value-only", como="get saldo   # el que estuvo aislado")
    p("  escrituras perdidas: ninguna (la de la minoría nunca se aceptó)")


def rcli(nodo, *a):
    return docker("exec", nodo, "redis-cli", *a)


def escritor(nodo, prefijo, segundos):
    """Escribe una clave cada 100 ms dentro del contenedor; al final imprime aceptadas, rechazadas y el último error."""
    script = (f"ok=0; mal=0; fin=$(( $(date +%s) + {segundos} )); i=0; "
              f"while [ $(date +%s) -lt $fin ]; do i=$((i+1)); "
              f"r=$(redis-cli SET {prefijo}:$i x 2>&1); "
              f"if [ \"$r\" = OK ]; then ok=$((ok+1)); else mal=$((mal+1)); ultimo=\"$r\"; fi; sleep 0.1; done; "
              f"echo \"$ok $mal $ultimo\"")
    return subprocess.Popen(["docker", "exec", nodo, "sh", "-c", script], stdout=subprocess.PIPE, text=True,
                            encoding="utf-8", env=ENV)


def resultado(proc):
    ok, mal, *resto = proc.communicate()[0].strip().split(" ", 2)
    return int(ok), int(mal), (resto[0] if resto else "")


def contar(nodo, prefijo):
    _, o = docker("exec", nodo, "sh", "-c", f"redis-cli --scan --pattern '{prefijo}:*' | wc -l")
    return int(o.strip() or 0)


def rol(nodo):
    _, o = rcli(nodo, "info", "replication")
    return next((l for l in o.splitlines() if l.startswith("role:")), "role:?")


def redis(minimo=False):
    docker("rm", "-f", "r1", "r2", *SENT)
    extra = ["--min-replicas-to-write", "1", "--min-replicas-max-lag", "10"] if minimo else []
    docker("run", "-d", "--name", "r1", "--network", RED, "--ip", R1, REDIS, "redis-server",
           "--appendonly", "no", *extra, check=True)
    docker("run", "-d", "--name", "r2", "--network", RED, "--ip", R2, REDIS, "redis-server",
           "--replicaof", R1, "6379", *extra, check=True)
    for n, ip in SENT.items():
        conf = (f"port 26379\nsentinel monitor m {R1} 6379 2\nsentinel down-after-milliseconds m 3000\n"
                f"sentinel failover-timeout m 10000\nsentinel announce-ip {ip}\n")
        docker("run", "-d", "--name", n, "--network", RED, "--ip", ip, REDIS, "sh", "-c",
               f"printf '{conf}' > /tmp/s.conf && exec redis-sentinel /tmp/s.conf", check=True)
    # listos de verdad: la réplica enganchada, y cada sentinel ve a los otros dos y no está en TILT
    for _ in range(240):
        listos = "master_link_status:up" in rcli("r2", "info", "replication")[1]
        for n in SENT:
            _, m = docker("exec", n, "redis-cli", "-p", "26379", "sentinel", "master", "m")
            _, inf = docker("exec", n, "redis-cli", "-p", "26379", "info", "sentinel")
            ls = m.splitlines()
            otros = ls[ls.index("num-other-sentinels") + 1] if "num-other-sentinels" in ls else "0"
            listos = listos and otros == "2" and "sentinel_tilt:0" in inf
        if listos:
            break
        time.sleep(1)
    else:
        raise SystemExit("[X] los sentinels no llegaron a verse entre sí (o siguen en TILT)")
    time.sleep(3)

    docker("network", "disconnect", RED, "r1", check=True)
    p(f"$ docker network disconnect {RED} r1   # el primario, aislado con sus clientes")
    t0 = time.time()
    en_r1 = escritor("r1", "minoria", 30)
    for _ in range(120):
        if rol("r2") == "role:master":
            break
        time.sleep(0.25)
    p(f"  los sentinels promueven a r2 a los {time.time() - t0:.1f} s ({rol('r2')})")
    ok2, mal2, _ = resultado(escritor("r2", "mayoria", 5))
    p(f"  5 s escribiendo en r2 (mayoría, el nuevo primario): aceptadas {ok2} · rechazadas {mal2}")
    ok, mal, ultimo = resultado(en_r1)
    p(f"  30 s escribiendo en r1 (minoría), que sigue creyéndose primario: aceptadas {ok} · rechazadas {mal}"
      + (f" · último error: {ultimo}" if mal else ""))
    antes = contar("r1", "minoria")
    p(f"  claves minoria:* en r1 antes de reconectar: {antes}")

    docker("network", "connect", "--ip", R1, RED, "r1", check=True)
    p(f"$ docker network connect {RED} r1")
    for _ in range(120):
        inf = rcli("r1", "info", "replication")[1]
        if "role:slave" in inf and "master_link_status:up" in inf and "master_sync_in_progress:0" in inf:
            break
        time.sleep(0.5)
    time.sleep(1)
    p(f"  r1 después: {rol('r1')} (los sentinels lo degradan a réplica de r2)")
    despues = contar("r1", "minoria")
    p(f"  claves minoria:* que quedan: {despues} · perdidas: {antes - despues} de {ok} aceptadas")
    p(f"  claves mayoria:* que quedan: {contar('r1', 'mayoria')} de {ok2}")


def main():
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    cab = ["# SALIDA — «System design: el teorema CAP» (cultura-devops, vídeo 353)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- etcd 3.6.5 (tres nodos) · {docker('run', '--rm', REDIS, 'redis-server', '--version')[1].split(' sha')[0]} "
           "(primario, réplica y tres sentinels, down-after 3 s)",
           "- la partición: `docker network disconnect`; los clientes escriben con `docker exec` dentro de cada lado.",
           "- una sola máquina."]
    salida.append("\n```")
    try:
        etcd()
        p("")
        p("== 3 · Redis: primario, réplica y tres sentinels. Se corta la red del primario ==")
        redis()
        p("")
        p("== 4 · Lo mismo con min-replicas-to-write 1 y min-replicas-max-lag 10 ==")
        redis(minimo=True)
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
