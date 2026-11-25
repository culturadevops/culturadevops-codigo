# -*- coding: utf-8 -*-
"""Tailscale vs NetBird vs Headscale — banco de pruebas del vídeo 340 (cultura-devops, serie versus).

La MISMA prueba para cada uno: un servidor de control propio y dos equipos que se unen a la red privada.
  · Headscale v0.29 (servidor de control libre) + dos clientes OFICIALES de Tailscale.
  · NetBird autoalojado (servidor combinado: management + signal + relay + STUN) + dos clientes NetBird.
  · Tailscale como servicio NO se mide: pide cuenta y clave de su web. Se cuenta con su documentación; los
    clientes son los mismos que aquí se unen a Headscale.

Mide, desde cero cada vez: qué corre en tu servidor (contenedores, imagen), cuánto tarda un equipo en unirse
y hablar con el otro, latencia y caudal por el túnel (iperf3, 3 rondas; la mediana) frente a la red directa,
memoria en reposo, y a quién se conecta cada uno fuera de tu servidor (DERP/STUN).

Todo en una sola máquina (Docker Desktop): el caudal mide el coste del túnel, no una red real.

    python correr.py
"""
import json
import re
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NET = "vpnlab"
HS_IMG, TS_IMG = "headscale/headscale:latest", "tailscale/tailscale:latest"
NBS_IMG, NB_IMG = "netbirdio/netbird-server:latest", "netbirdio/netbird:latest"
IPERF, CURL = "networkstatic/iperf3:latest", "curlimages/curl:latest"
CONTENEDORES = ["headscale", "ts1", "ts2", "nb-server", "nb1", "nb2", "ip-ts2", "ip-nb2", "ip-dir"]
salida = []


def sh(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       env={**__import__("os").environ, "MSYS_NO_PATHCONV": "1"})
    return (r.stdout + r.stderr).strip()


def limpio(t):
    return re.sub(r"\x1b\[[0-9;]*m", "", t)


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", limpio(texto).strip(), "```"])
    print(f"--- {titulo}\n{limpio(texto).strip()[:1500]}\n", flush=True)


def seccion(t):
    salida.extend(["", f"## {t}"])
    print(f"\n===== {t}", flush=True)


def win(p):
    return sh(["cygpath", "-w", str(p)]) if p.drive == "" else str(p)


def reset():
    sh(["docker", "rm", "-f", *CONTENEDORES])
    sh(["docker", "volume", "rm", "-f", "hs-data", "nb-data"])
    sh(["docker", "network", "rm", NET])
    sh(["docker", "network", "create", NET])


def espera(pred, tope=120, paso=0.25):
    t0 = time.time()
    while time.time() - t0 < tope:
        if pred():
            return time.time() - t0
        time.sleep(paso)
    return None


def ping_ok(cont, ip):
    return " 0% packet loss" in sh(["docker", "exec", cont, "ping", "-c", "1", "-W", "1", ip], timeout=10)


def iperf(cliente, ip):
    r = sh(["docker", "run", "--rm", "--network", f"container:{cliente}", IPERF, "-c", ip, "-t", "8", "-J"], timeout=60)
    try:
        return json.loads(r)["end"]["sum_received"]["bits_per_second"] / 1e9
    except Exception:
        return None


def ping_rtt(cont, ip):
    r = sh(["docker", "exec", cont, "ping", "-c", "20", "-i", "0.2", "-q", ip], timeout=60)
    m = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)", r)
    return (float(m.group(2)), r.splitlines()[-1]) if m else (None, r)


def mem(cont):
    return sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", cont])


def tam(img):
    b = int(sh(["docker", "image", "inspect", "-f", "{{.Size}}", img]) or 0)
    return f"{b / 1e6:.1f} MB"


# ── Headscale + clientes Tailscale ───────────────────────────────────────
def headscale():
    seccion("2 · Headscale + dos clientes de Tailscale")
    cfg = AQUI / "headscale" / "config.yaml"
    t0 = time.time()
    sh(["docker", "run", "-d", "--name", "headscale", "--network", NET, "-v", f"{win(cfg)}:/etc/headscale/config.yaml:ro",
        "-v", "hs-data:/var/lib/headscale", HS_IMG, "serve"])
    listo = espera(lambda: "listening and serving HTTP" in sh(["docker", "logs", "headscale"]))
    anota("arrancar el servidor", "docker run headscale/headscale serve",
          f"servidor listo en {listo:.1f} s\n" + "\n".join(l for l in limpio(sh(['docker', 'logs', 'headscale'])).splitlines()
                                                      if "starting headscale" in l or "serving HTTP" in l))
    sh(["docker", "exec", "headscale", "headscale", "users", "create", "lab"])
    clave = limpio(sh(["docker", "exec", "headscale", "headscale", "preauthkeys", "create", "-u", "1", "--reusable",
                       "-e", "2h"])).splitlines()[-1].strip()
    anota("usuario y clave de alta", "headscale users create lab; headscale preauthkeys create -u 1 --reusable",
          f"clave: {clave[:14]}… (reutilizable, 2 h)")
    t1 = time.time()
    for n in ("ts1", "ts2"):
        sh(["docker", "run", "-d", "--name", n, "--hostname", n, "--network", NET, "--cap-add", "NET_ADMIN",
            "--device", "/dev/net/tun", "-e", f"TS_AUTHKEY={clave}", "-e", "TS_EXTRA_ARGS=--login-server=http://headscale:8080",
            "-e", "TS_USERSPACE=false", "-e", "TS_STATE_DIR=/var/lib/tailscale", TS_IMG])
    unido = espera(lambda: "100.64.0.2" in sh(["docker", "exec", "ts1", "tailscale", "status"]))
    habla = espera(lambda: ping_ok("ts1", "100.64.0.2"))
    anota("dos equipos se unen y se hablan", "docker run tailscale/tailscale (TS_AUTHKEY, --login-server)",
          f"ts2 visible para ts1: {unido:.1f} s desde arrancar los clientes\nprimer ping por el túnel: {habla:.1f} s después\n"
          + sh(["docker", "exec", "ts1", "tailscale", "status"]))
    anota("lo que guarda el servidor", "headscale nodes list",
          sh(["docker", "exec", "headscale", "headscale", "nodes", "list"]))
    anota("¿a quién más se conecta el cliente?", "grep derp config.yaml; tailscale netcheck",
          "config.yaml (por defecto):\n" + "\n".join(l for l in cfg.read_text(encoding="utf-8").splitlines() if "controlplane" in l)
          + "\n\n" + "\n".join(l for l in sh(["docker", "exec", "ts1", "tailscale", "netcheck"]).splitlines()
                               if "Nearest DERP" in l or "UDP" in l))
    return t0


# ── NetBird autoalojado ─────────────────────────────────────────────────
def netbird():
    seccion("3 · NetBird autoalojado + dos clientes")
    cfg = AQUI / "netbird" / "config.yaml"
    sh(["docker", "run", "-d", "--name", "nb-server", "--network", NET, "-e", "NB_SETUP_PAT_ENABLED=true",
        "-v", "nb-data:/var/lib/netbird", "-v", f"{win(cfg)}:/etc/netbird/config.yaml:ro", NBS_IMG,
        "--config", "/etc/netbird/config.yaml"])

    def api(metodo, ruta, cuerpo=None, token=None):
        c = ["docker", "run", "--rm", "--network", NET, CURL, "-s", "-X", metodo, f"http://nb-server:80{ruta}",
             "-H", "Content-Type: application/json"]
        if token:
            c += ["-H", f"Authorization: Token {token}"]
        if cuerpo:
            c += ["-d", json.dumps(cuerpo)]
        return sh(c)
    def responde():
        r = sh(["docker", "run", "--rm", "--network", NET, CURL, "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "http://nb-server:80/api/users"])
        return r.strip().endswith("401")
    listo = espera(responde, tope=180, paso=0.5)
    logs = limpio(sh(["docker", "logs", "nb-server"]))
    anota("arrancar el servidor", "docker run netbirdio/netbird-server --config config.yaml",
          f"API respondiendo en {listo:.1f} s\n" + "\n".join(l.split(" INFO ")[-1] for l in logs.splitlines()
                                                      if "Exposed address" in l or "Signal URI" in l or "will be downloaded" in l))
    r = json.loads(api("POST", "/api/setup", {"email": "admin@lab.internal", "name": "Admin",
                                               "password": "una-clave-larga-de-prueba-123", "create_pat": True,
                                               "pat_expire_in": 1}))
    token = r["personal_access_token"]
    k = json.loads(api("POST", "/api/setup-keys", {"name": "lab", "type": "reusable", "expires_in": 86400,
                                                   "auto_groups": [], "usage_limit": 0}, token))
    anota("administrador y clave de alta", "POST /api/setup; POST /api/setup-keys",
          f"usuario: {r['email']} · token: {token[:8]}…\nclave de alta: {k['key'][:9]}… tipo {k['type']}, válida: {k['valid']}")
    for n in ("nb1", "nb2"):
        sh(["docker", "run", "-d", "--name", n, "--hostname", n, "--network", NET, "--cap-add", "NET_ADMIN",
            "--cap-add", "SYS_ADMIN", "--cap-add", "SYS_RESOURCE", "--device", "/dev/net/tun",
            "-e", f"NB_SETUP_KEY={k['key']}", "-e", "NB_MANAGEMENT_URL=http://nb-server:80", NB_IMG])

    def ip_de(n):
        try:
            return json.loads(sh(["docker", "exec", n, "netbird", "status", "--json"]))["netbirdIp"].split("/")[0]
        except Exception:
            return ""
    def ve_al_otro():
        try:
            return json.loads(sh(["docker", "exec", "nb1", "netbird", "status", "--json"]))["peers"]["total"] >= 1
        except Exception:
            return False
    unido = espera(lambda: bool(ip_de("nb2")) and ve_al_otro())
    ip2 = ip_de("nb2")
    habla = espera(lambda: ping_ok("nb1", ip2))
    anota("dos equipos se unen y se hablan", "docker run netbirdio/netbird (NB_SETUP_KEY, NB_MANAGEMENT_URL)",
          f"nb2 visible para nb1: {unido:.1f} s desde arrancar los clientes\nprimer ping por el túnel: {habla:.1f} s después\n"
          + "\n".join(l for l in sh(["docker", "exec", "nb1", "netbird", "status"]).splitlines()
                      if l.split(":")[0] in ("Management", "Signal", "Relays", "NetBird IP", "Interface type", "Lazy connection", "Peers count")))
    anota("¿a quién más se conecta el cliente?", "netbird status -d",
          "\n".join(l for l in sh(["docker", "exec", "nb1", "netbird", "status", "-d"]).splitlines()
                    if "stun:" in l or "rel://" in l or "Connection type" in l or "ICE candidate (" in l))
    anota("lo que guarda el servidor", "GET /api/peers",
          "\n".join(f"{p['hostname']}  {p['ip']}  conectado={p['connected']}" for p in json.loads(api("GET", "/api/peers", token=token))))
    return ip2


def medir(ip_nb2):
    seccion("4 · El túnel: latencia y caudal (misma máquina)")
    ip_dir = sh(["docker", "inspect", "-f", '{{(index .NetworkSettings.Networks "vpnlab").IPAddress}}', "ts2"])
    for nombre, cont in (("ip-ts2", "ts2"), ("ip-nb2", "nb2")):
        sh(["docker", "run", "-d", "--name", nombre, "--network", f"container:{cont}", IPERF, "-s"])
    time.sleep(2)
    # MISMO ESTADO en los dos: conexión directa entre equipos, no por el retransmisor (en una corrida NetBird
    # salió «Relayed» y Tailscale «direct»: compararlos así mide cosas distintas).
    def nb_p2p():
        ping_ok("nb1", ip_nb2)
        return "Connection type: P2P" in sh(["docker", "exec", "nb1", "netbird", "status", "-d"])

    def ts_directo():
        ping_ok("ts1", "100.64.0.2")
        return "direct" in sh(["docker", "exec", "ts1", "tailscale", "status"])
    if espera(nb_p2p, tope=120, paso=2) is None or espera(ts_directo, tope=60, paso=2) is None:
        raise SystemExit("[X] no están los dos en conexión directa: no se compara")
    anota("los dos van directos antes de medir", "tailscale status; netbird status -d",
          "Tailscale: " + [l for l in sh(["docker", "exec", "ts1", "tailscale", "status"]).splitlines() if "ts2" in l][0].strip()
          + "\nNetBird:   " + [l.strip() for l in sh(["docker", "exec", "nb1", "netbird", "status", "-d"]).splitlines()
                              if "Connection type" in l][0])
    casos = [("Red directa de Docker", "ts1", ip_dir), ("Tailscale + Headscale", "ts1", "100.64.0.2"),
             ("NetBird", "nb1", ip_nb2)]
    filas = []
    for nombre, cli, ip in casos:
        rtt, linea = ping_rtt(cli, ip)
        rondas = [iperf(cli, ip) for _ in range(3)]
        ok = [x for x in rondas if x]
        filas.append(f"{nombre:24} ping medio {rtt:.3f} ms · iperf3 (3 rondas, Gbit/s): "
                     + ", ".join(f"{x:.2f}" for x in ok) + f" · mediana {statistics.median(ok):.2f}")
    anota("latencia (20 pings) y caudal (iperf3, 8 s)", "ping -c 20; iperf3 -c <ip> -t 8  ×3", "\n".join(filas))
    anota("tipo de interfaz", "ip link; netbird status",
          "tailscale0: " + sh(["docker", "exec", "ts1", "sh", "-c", "ip -d link show tailscale0 | sed -n 2,3p"]) + "\n"
          + "\n".join(l for l in sh(["docker", "exec", "nb1", "netbird", "status"]).splitlines() if "Interface type" in l))


def recursos():
    seccion("5 · Lo que corre en tu servidor")
    anota("memoria en reposo (2 equipos unidos)", "docker stats --no-stream",
          "\n".join(mem(c) for c in ("headscale", "nb-server", "ts1", "nb1")))
    anota("tamaño de las imágenes", "docker image inspect -f {{.Size}}",
          "\n".join(f"{i:36} {tam(i)}" for i in (HS_IMG, NBS_IMG, TS_IMG, NB_IMG)))


def main():
    reset()
    seccion("1 · Versiones")
    anota("versiones", "headscale version; tailscale version; netbird version",
          limpio(sh(["docker", "run", "--rm", HS_IMG, "version"])).splitlines()[0] + "\n"
          + "tailscale " + sh(["docker", "run", "--rm", "--entrypoint", "tailscale", TS_IMG, "version"]).splitlines()[0] + "\n"
          + "netbird " + sh(["docker", "run", "--rm", "--entrypoint", "netbird", NB_IMG, "version"]).splitlines()[0])
    headscale()
    ip_nb2 = netbird()
    time.sleep(10)
    medir(ip_nb2)
    recursos()
    cab = [f"# SALIDA — Tailscale vs NetBird vs Headscale (vídeo 340)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. Una sola máquina (Docker "
           f"Desktop, WSL2): el caudal mide el coste del túnel, no una red real. Tailscale como servicio no se mide (pide cuenta)."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")
    print("SALIDA.md escrita")
    reset()


if __name__ == "__main__":
    main()
