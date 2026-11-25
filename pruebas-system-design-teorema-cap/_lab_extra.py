
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
