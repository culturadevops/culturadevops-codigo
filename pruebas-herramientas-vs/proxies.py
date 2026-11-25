# -*- coding: utf-8 -*-
"""proxies.py — banco de los proxies de la serie «¿X o Y? Lo medí» de herramientas (cultura-devops, pedido del dueño 2026-11-05).

    python proxies.py nginx caddy      → nginx-caddy/SALIDA.md      (vídeo 836: estático + proxy, HTTP y HTTPS)
    python proxies.py traefik nginx    → traefik-nginx/SALIDA.md    (vídeo 837: proxy, HTTP y HTTPS)
    python proxies.py haproxy nginx    → haproxy-nginx/SALIDA.md    (vídeo 838: proxy, HTTP y HTTPS)
    python proxies.py ... --preparar   → solo construye las imágenes (sin candado, sin medir)

Montaje (igual para los dos lados):
  · el proxy, con imagen OFICIAL fijada y la config de proxies/ copiada dentro, limitado a 2 CPU y 1 GiB, y 2 procesos/hilos
    de trabajo (nginx worker_processes 2, haproxy nbthread 2, GOMAXPROCS=2 en Caddy y Traefik);
  · detrás, un backend Go que devuelve siempre el mismo cuerpo de 1 KiB (6 CPU: el cuello debe ser el proxy; se mide su techo);
  · la carga, con wrk (64 conexiones, 4 hilos) desde OTRO contenedor de la misma red; latencia a ritmo fijo con hey;
  · el MISMO certificado ECDSA P-256 para HTTPS;
  · antes de medir: misma respuesta (código, tamaño y sha256 del cuerpo) por cada ruta en los dos; si no, exit 1.
"""
import re
import sys
import time
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as K  # noqa: E402
from comun import w, sh, ok, num  # noqa: E402

AQUI = K.AQUI
PX = AQUI / "proxies"
HEY = "golandia-revancha-hey:1"   # hey v0.1.4 en scratch (canales/golandia/recursos/pruebas-go-java-revancha)
WRK = "hvs-wrk:1"
BACK = "hvs-backend:1"
C, C_MUCHAS, SEG, SEG_CAL, REPES = 64, 1000, 20, 5, 5

P = {
    "nginx": dict(nombre="Nginx", oficial="nginx:1.30.6-alpine", img="hvs-nginx:1",
                  df="FROM nginx:1.30.6-alpine\nCOPY nginx.conf /etc/nginx/nginx.conf\nCOPY certs /etc/certs\nCOPY www /srv/www\n",
                  env={}, version=["nginx", "-v"], estatico=True),
    # «de fábrica»: el mismo proxy SIN tocar el pool de conexiones al backend (solo en la prueba de 1.000 conexiones)
    "nginx-fab": dict(nombre="Nginx de fábrica (sin keepalive al backend)", oficial="nginx:1.30.6-alpine", img="hvs-nginx-fab:1",
                      df="FROM nginx:1.30.6-alpine\nCOPY nginx-fabrica.conf /etc/nginx/nginx.conf\nCOPY certs /etc/certs\nCOPY www /srv/www\n",
                      env={}, version=["nginx", "-v"], estatico=True),
    "caddy-fab": dict(nombre="Caddy de fábrica (pool de 32)", oficial="caddy:2.11.8-alpine", img="hvs-caddy-fab:1",
                      df="FROM caddy:2.11.8-alpine\nCOPY Caddyfile-fabrica /etc/caddy/Caddyfile\nCOPY certs /etc/certs\nCOPY www /srv/www\n",
                      env={"GOMAXPROCS": "2"}, version=["caddy", "version"], estatico=True),
    "traefik-fab": dict(nombre="Traefik de fábrica (pool de 200)", oficial="traefik:v3.7.17", img="hvs-traefik-fab:1",
                        df="FROM traefik:v3.7.17\nCOPY traefik-fabrica.yml /etc/traefik/traefik.yml\nCOPY dinamica.yml /etc/traefik/dinamica.yml\n"
                           "COPY certs /etc/certs\n",
                        env={"GOMAXPROCS": "2"}, version=["traefik", "version"], estatico=False),
    "caddy": dict(nombre="Caddy", oficial="caddy:2.11.8-alpine", img="hvs-caddy:1",
                  df="FROM caddy:2.11.8-alpine\nCOPY Caddyfile /etc/caddy/Caddyfile\nCOPY certs /etc/certs\nCOPY www /srv/www\n",
                  env={"GOMAXPROCS": "2"}, version=["caddy", "version"], estatico=True),
    "traefik": dict(nombre="Traefik", oficial="traefik:v3.7.17", img="hvs-traefik:1",
                    df="FROM traefik:v3.7.17\nCOPY traefik.yml /etc/traefik/traefik.yml\nCOPY dinamica.yml /etc/traefik/dinamica.yml\n"
                       "COPY certs /etc/certs\n",
                    env={"GOMAXPROCS": "2"}, version=["traefik", "version"], estatico=False),
    "haproxy": dict(nombre="HAProxy", oficial="haproxy:3.4.7-alpine", img="hvs-haproxy:1",
                    df="FROM haproxy:3.4.7-alpine\nCOPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg\nCOPY certs /etc/certs\n",
                    env={}, version=["haproxy", "-v"], estatico=False),
}


def construir(claves):
    ok(["docker", "build", "-q", "-t", BACK, str(AQUI / "_comun" / "backend")])
    ok(["docker", "build", "-q", "-f", str(AQUI / "_comun" / "Dockerfile.wrk"), "-t", WRK, str(AQUI / "_comun")])
    assert sh(["docker", "image", "inspect", HEY]).returncode == 0, f"falta {HEY} (se construye con pruebas_go_java_revancha.py)"
    for k in claves:
        f = PX / f"Dockerfile.{k}"
        f.write_text(P[k]["df"], encoding="utf-8")
        ok(["docker", "build", "-q", "-f", str(f), "-t", P[k]["img"], str(PX)])


def rutas(a, b):
    r = [("/api", "http"), ("/api", "https")]
    if P[a]["estatico"] and P[b]["estatico"]:
        r = [("/static/archivo.html", "http"), ("/static/archivo.html", "https")] + r
    return r


def url(ruta, esquema):
    return f"{esquema}://proxy:{8080 if esquema == 'http' else 8443}{ruta}"


def nombre_ruta(ruta, esquema):
    return ("estático 4 KiB" if "static" in ruta else "proxy /api (1 KiB)") + (" · HTTPS" if esquema == "https" else " · HTTP")


def backend_arriba():
    K.rm("backend")
    ok(["docker", "run", "-d", "--rm", "--name", "backend", "--network", K.RED, "--cpus", "6", BACK])
    time.sleep(1)


def arrancar(k):
    K.rm("proxy")
    args = ["docker", "run", "-d", "--rm", "--name", "proxy", "--network", K.RED, "--cpus", K.CPUS, "--memory", K.MEM,
            "-p", "9301:8080", "-p", "9302:8443"]
    for e, v in P[k]["env"].items():
        args += ["-e", f"{e}={v}"]
    t0 = time.perf_counter()
    ok(args + [P[k]["img"]])
    return t0


def esperar_200(t0):
    while True:
        try:
            with urllib.request.urlopen("http://127.0.0.1:9301/api", timeout=1) as r:
                if r.status == 200:
                    r.read()
                    return (time.perf_counter() - t0) * 1000
        except Exception:
            pass
        if time.perf_counter() - t0 > 30:
            logs = sh(["docker", "logs", "proxy"])
            raise SystemExit(f"⛔ el proxy no arrancó:\n{logs.stdout[-1500:]}\n{logs.stderr[-1500:]}")
        time.sleep(0.005)


def en_red(cmd):
    return ok(["docker", "run", "--rm", "--network", K.RED, "--entrypoint", "sh", WRK, "-c", cmd]).stdout


def wrk(u, conexiones, seg):
    r = sh(["docker", "run", "--rm", "--network", K.RED, "--cpus", "6", WRK, "wrk", "-t4", f"-c{conexiones}", f"-d{seg}s",
            "--timeout", "5s", "--latency", u])
    t = r.stdout
    if r.returncode != 0 or "Requests/sec" not in t:
        raise SystemExit(f"⛔ wrk falló contra {u}:\n{t[-1500:]}\n{r.stderr[-1500:]}")
    rps = float(re.search(r"Requests/sec:\s+([\d.]+)", t).group(1))
    lat = {}
    for q in (50, 99):
        m = re.search(rf"^\s+{q}%\s+([\d.]+)(us|ms|s)\s*$", t, re.M)
        lat[q] = K.ms(m.group(1), m.group(2))
    no2xx = int(m.group(1)) if (m := re.search(r"Non-2xx or 3xx responses:\s+(\d+)", t)) else 0
    m = re.search(r"Socket errors: connect (\d+), read (\d+), write (\d+), timeout (\d+)", t)
    tipos = dict(zip(("connect", "read", "write", "timeout"), map(int, m.groups()))) if m else {}
    errs = sum(tipos.values())
    det = " · ".join([f"{k} {v}" for k, v in tipos.items() if v] + ([f"no-2xx {no2xx}"] if no2xx else []))
    return dict(rps=rps, p50=lat[50], p99=lat[99], no2xx=no2xx, errs=errs, det=det or "0",
                total=int(re.search(r"(\d+) requests in", t).group(1)))


def log_errores():
    """Resumen del log de errores del proxy: los mensajes, sin fecha ni números variables, con cuántas veces salió cada uno."""
    r = sh(["docker", "logs", "proxy"])
    cuenta = {}
    for linea in (r.stdout + r.stderr).splitlines():
        if not re.search(r"error|warn|crit|alert", linea, re.I):
            continue
        clave = re.sub(r"\d+", "N", re.sub(r"^\S+ \S+ ", "", linea))[:140]
        cuenta[clave] = cuenta.get(clave, 0) + 1
    return sorted(cuenta.items(), key=lambda x: -x[1])[:3]


def hey(u, qps, seg=15, workers=50):
    r = sh(["docker", "run", "--rm", "--network", K.RED, "--cpus", "4", HEY, "-z", f"{seg}s", "-c", str(workers),
            "-q", f"{qps / workers:.2f}", u])
    t = r.stdout
    rps = float(re.search(r"Requests/sec:\s+([\d.]+)", t).group(1))
    lat = {q: float(re.search(rf"\s{q}% in ([\d.]+) secs", t).group(1)) * 1000 for q in (50, 99)}
    codigos = re.findall(r"\[(\d+)\]\s+(\d+) responses", t)
    assert codigos and all(c == "200" for c, _ in codigos), f"códigos raros: {codigos}\n{t[-800:]}"
    return dict(rps=rps, p50=lat[50], p99=lat[99])


def mismo_resultado(a, b, rs):
    w("## 0 · ¿Hacen lo mismo? (antes de medir)\n")
    import hashlib
    esperado = {"/static/archivo.html": hashlib.sha256((PX / "www" / "static" / "archivo.html").read_bytes()).hexdigest()}
    backend_arriba()
    esperado["/api"] = en_red("curl -s http://backend:9000/api | sha256sum").split()[0]
    w(f"- Esperado: /api = sha256 {esperado['/api'][:16]}… (backend directo, 1.024 bytes)" +
      (f"; /static/archivo.html = sha256 {esperado['/static/archivo.html'][:16]}… (4.096 bytes)" if len(rs) > 2 else ""))
    for k in (a, b):
        t0 = arrancar(k)
        esperar_200(t0)
        for ruta, esq in rs:
            u = url(ruta, esq)
            linea = en_red(f"curl -sk -o /tmp/c -w '%{{http_code}} %{{size_download}} %{{http_version}}' {u}; echo; sha256sum /tmp/c").split()
            cod, tam, ver, h = linea[0], linea[1], linea[2], linea[3]
            igual = cod == "200" and h == esperado[ruta]
            w(f"- {P[k]['nombre']} {esq.upper()} {ruta}: {cod}, {tam} bytes, HTTP/{ver}, sha256 {h[:16]}… → "
              f"{'igual' if igual else '⛔ DISTINTO'}")
            if not igual:
                raise SystemExit("los dos lados no devuelven lo mismo: no se compara")
        tls = en_red("echo | openssl s_client -connect proxy:8443 -servername proxy 2>/dev/null | grep -E '^New,'").strip()
        w(f"- {P[k]['nombre']} TLS negociado con el cliente de carga: `{tls}`")
        K.rm("proxy")
    w()


def arranque(a, b):
    w(f"## 2 · Arranque y memoria en reposo (contenedor nuevo → primera respuesta 200 por el proxy; mediana de {REPES})\n")
    w("| proxy | 1.ª respuesta (Docker incluido) | memoria en reposo |")
    w("|---|---|---|")
    res = {}
    for k in (a, b):
        ts, mems = [], []
        for _ in range(REPES):
            t0 = arrancar(k)
            ts.append(esperar_200(t0))
            time.sleep(2)
            mems.append(K.stats("proxy")[0])
            K.rm("proxy")
        res[k] = (K.mediana(ts), K.mediana(mems))
        w(f"| {P[k]['nombre']} | {num(res[k][0], 0)} ms | {num(res[k][1])} MiB |")
    w()
    return res


def carga(a, b, rs):
    w(f"## 3 · A tope: wrk con {C} conexiones (4 hilos), {SEG} s tras {SEG_CAL} s de calentamiento\n")
    w("Proxy con 2 CPU y 1 GiB. Memoria = máximo de `docker stats` durante la carga; CPU = media (200 % = las 2 CPU llenas). "
      "Errores = los que cuenta wrk (de socket por tipo y respuestas no 2xx) sobre todas las peticiones de la corrida.\n")
    w("| ruta | proxy | peticiones/s | p50 | p99 | memoria máx. | CPU media | errores |")
    w("|---|---|---|---|---|---|---|---|")
    res = {}
    for k in (a, b):
        t0 = arrancar(k)
        esperar_200(t0)
        for ruta, esq in rs:
            u = url(ruta, esq)
            wrk(u, C, SEG_CAL)
            with K.Muestreo("proxy") as m:
                r = wrk(u, C, SEG)
            r.update(mem=m.mem_max, cpu=m.cpu_media)
            res[(k, ruta, esq)] = r
        K.rm("proxy")
    for ruta, esq in rs:
        for k in (a, b):
            r = res[(k, ruta, esq)]
            w(f"| {nombre_ruta(ruta, esq)} | {P[k]['nombre']} | {num(r['rps'], 0)} | {num(r['p50'], 2)} ms | {num(r['p99'], 2)} ms | "
              f"{num(r['mem'])} MiB | {num(r['cpu'], 0)} % | {r['det']} de {num(r['total'], 0)} |")
    w()
    return res


def muchas(a, b):
    w(f"## 4 · Muchas conexiones: wrk con {C_MUCHAS} conexiones abiertas a la vez, proxy /api por HTTP, {SEG} s\n")
    w("Arriba, la config del banco (pool de 1.024 conexiones ociosas al backend en todos). Abajo, cada proxy «de fábrica», sin "
      "tocar ese pool: Nginx sin upstream keepalive (una conexión nueva por petición), Caddy con su pool de 32 y Traefik con el de "
      "200 (valores de su documentación); HAProxy no tiene tope de fábrica y no lleva variante. Es lo ÚNICO que cambia "
      "(proxies/*-fabrica.*). Con 1.000 clientes, lo que no cabe en el pool se abre y se cierra en cada petición.\n")
    w("| proxy | peticiones/s | p50 | p99 | memoria máx. | errores (wrk) |")
    w("|---|---|---|---|---|---|")
    res, logs = {}, {}
    variantes = list((a, b)) + [k + "-fab" for k in (a, b) if k + "-fab" in P]
    for k in variantes:
        t0 = arrancar(k)
        esperar_200(t0)
        u = url("/api", "http")
        wrk(u, C_MUCHAS, SEG_CAL)
        with K.Muestreo("proxy") as m:
            r = wrk(u, C_MUCHAS, SEG)
        r.update(mem=m.mem_max)
        res[k] = r
        logs[k] = log_errores()
        K.rm("proxy")
        w(f"| {P[k]['nombre']} | {num(r['rps'], 0)} | {num(r['p50'], 2)} ms | {num(r['p99'], 2)} ms | {num(r['mem'])} MiB | "
          f"{r['det']} de {num(r['total'], 0)} |")
    w("\nLo que dejó cada proxy en su log de errores durante esta prueba (los 3 mensajes más repetidos; N = número):\n")
    for k in variantes:
        w(f"- {P[k]['nombre']}: " + ("; ".join(f"{n}× `{msg}`" for msg, n in logs[k]) if logs[k] else "nada"))
    w()
    return res


def ritmo_fijo(a, b, rs, tope):
    w("## 5 · El mismo tráfico para los dos: ritmo fijo con hey (50 clientes, 15 s)\n")
    w("Ritmo = la mitad de lo que aguantó el más lento en esa ruta (a tope la latencia sale de la cola). Aquí lo que cuenta es "
      "cuánta CPU gasta cada uno para servir LO MISMO, y la latencia sin cola.\n")
    w("| ruta | ritmo pedido | proxy | peticiones/s servidas | p50 | p99 | CPU media | memoria máx. |")
    w("|---|---|---|---|---|---|---|---|")
    res = {}
    for ruta, esq in rs:
        qps = round(min(tope[(k, ruta, esq)]["rps"] for k in (a, b)) / 2 / 100) * 100
        for k in (a, b):
            t0 = arrancar(k)
            esperar_200(t0)
            u = url(ruta, esq)
            hey(u, qps, seg=5)
            with K.Muestreo("proxy") as m:
                r = hey(u, qps)
            r.update(mem=m.mem_max, cpu=m.cpu_media, qps=qps)
            res[(k, ruta, esq)] = r
            K.rm("proxy")
            w(f"| {nombre_ruta(ruta, esq)} | {num(qps, 0)}/s | {P[k]['nombre']} | {num(r['rps'], 0)} | {num(r['p50'], 2)} ms | "
              f"{num(r['p99'], 2)} ms | {num(r['cpu'], 0)} % | {num(r['mem'])} MiB |")
    w()
    return res


def main():
    a, b = sys.argv[1], sys.argv[2]
    par = f"{a}-{b}"
    K.red()
    construir((a, b) + tuple(k + "-fab" for k in (a, b) if k + "-fab" in P))
    if "--preparar" in sys.argv:
        print("[ok] imágenes listas")
        return
    rs = rutas(a, b)
    K.OUT.clear()
    with K.candado(par):
        w(f"# SALIDA — ¿{P[a]['nombre']} o {P[b]['nombre']}? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)\n")
        w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}, bajo el candado _logs/banco.lock. Regenerable con "
          f"`python proxies.py {a} {b}`. ⛔ Ninguna cifra de blog: todo salió de aquí.\n")
        for k in (a, b):
            v = sh(["docker", "run", "--rm", "--entrypoint", P[k]["version"][0], P[k]["img"]] + P[k]["version"][1:])
            w(f"- {P[k]['nombre']}: `{(v.stdout + v.stderr).strip().splitlines()[0]}` — imagen oficial `{P[k]['oficial']}`")
        w(f"- Docker `{sh(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip()}` (Docker Desktop, Windows 11, 24 hilos). "
          f"Proxy con {K.CPUS} CPU y {K.MEM}, 2 procesos/hilos de trabajo; backend Go con 6 CPU; wrk con 6 CPU; hey con 4.")
        w("- Configs en proxies/: sin registro de accesos en ninguno, conexiones persistentes al backend en todos con un pool de 1.024 "
          "ociosas (Nginx keepalive 1024, Caddy keepalive_idle_conns_per_host 1024, Traefik maxIdleConnsPerHost 1024; HAProxy sin tope "
          "de fábrica), el mismo "
          "certificado ECDSA P-256 en HTTPS. wrk habla HTTP/1.1 (sin HTTP/2 ni HTTP/3).\n")
        mismo_resultado(a, b, rs)
        w("## 1 · Lo que despliegas (imagen oficial, sin la config)\n")
        w("| proxy | imagen | tamaño en disco |")
        w("|---|---|---|")
        for k in (a, b):
            w(f"| {P[k]['nombre']} | `{P[k]['oficial']}` | {num(K.tam_imagen(P[k]['oficial']))} MiB |")
        w()
        back = wrk("http://backend:9000/api", C, 10)
        w(f"Techo del backend solo (wrk directo, sin proxy, 10 s): {num(back['rps'], 0)} pet/s, p50 {num(back['p50'], 2)} ms. "
          "Si un proxy se acercara a esa cifra, el cuello sería el backend.\n")
        arranque(a, b)
        tope = carga(a, b, rs)
        muchas(a, b)
        ritmo_fijo(a, b, [r for r in rs if r[0] == "/api"] + [r for r in rs if r[0] != "/api"], tope)
        K.rm("proxy", "backend")
    K.guardar(AQUI / par / "SALIDA.md")


if __name__ == "__main__":
    main()
