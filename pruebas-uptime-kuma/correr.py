# -*- coding: utf-8 -*-
"""Uptime Kuma — banco de pruebas del vídeo 326 (cultura-devops, serie herramientas).

Uptime Kuma 2.x + nginx (web) + redis + ntfy propio (las alertas), en la red Docker `uk`.
Se configura por socket.io con cliente.py (la librería uptime-kuma-api no habla con la 2.x).
Los latidos se leen de la propia base SQLite de Kuma; las alertas, del tema de ntfy.
Las capturas del panel salen con Playwright (capturar.js) a motor/remotion/public/.

    python correr.py
"""
import json
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\uptime-kuma")
KUMA = "louislam/uptime-kuma:2"
salida = []


def sh(cmd, timeout=600, entrada=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:900]}\n", flush=True)


def cliente(*args):
    return sh(["docker", "run", "--rm", "--network", "uk", "-v", f"{AQUI}:/w", "kuma-cliente",
               "python", "/w/cliente.py", *args])


def latidos(n=2):
    tmp = Path(tempfile.mkdtemp())
    for f in ("kuma.db", "kuma.db-wal", "kuma.db-shm"):
        sh(["docker", "cp", f"kuma:/app/data/{f}", str(tmp / f)])
    con = sqlite3.connect(tmp / "kuma.db")
    filas = con.execute(
        "SELECT m.name, h.status, h.ping, h.msg, h.time FROM heartbeat h JOIN monitor m "
        "ON m.id=h.monitor_id ORDER BY h.time DESC, m.id").fetchall()
    con.close()
    vistos, txt = {}, []
    for nombre, st, ping, msg, t in filas:
        if vistos.get(nombre, 0) >= n:
            continue
        vistos[nombre] = vistos.get(nombre, 0) + 1
        txt.append(f"{t[11:19]}  {nombre:<12} {'UP  ' if st == 1 else 'DOWN'}  "
                   f"{(str(ping) + ' ms') if ping is not None else '-':>8}  {(msg or '')[:60]}")
    return "\n".join(sorted(txt))


def ntfy():
    raw = sh(["docker", "run", "--rm", "--network", "uk", "curlimages/curl", "-s",
              "http://ntfy/alertas/json?poll=1"])
    out = []
    for linea in raw.splitlines():
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        out.append(f"{datetime.fromtimestamp(d['time'], timezone.utc):%H:%M:%S}  "
                   f"prio={d.get('priority', 3)}  {d.get('title', '')} | {d.get('message', '')[:90]}")
    return "\n".join(out) or "(sin mensajes)"


def captura(nombre, ruta=""):
    PUB.mkdir(parents=True, exist_ok=True)
    print(sh(["node", str(AQUI / "capturar.js"), str(PUB / f"{nombre}.png"), *([ruta] if ruta else [])]))


def main():
    sh(["docker", "rm", "-f", "kuma", "web", "redis", "ntfy"])
    sh(["docker", "network", "rm", "uk"])
    sh(["docker", "network", "create", "uk"])
    print(sh(["docker", "build", "-q", "-t", "kuma-cliente", "-"], timeout=900, entrada=(
        "FROM python:3.12-slim\nRUN pip install -q 'python-socketio[client]' websocket-client\n")))

    salida.append("\n## 1 · Levantar Uptime Kuma y los servicios a vigilar")
    sh(["docker", "run", "-d", "--name", "web", "--network", "uk", "nginx:alpine"])
    sh(["docker", "run", "-d", "--name", "redis", "--network", "uk", "redis:alpine"])
    sh(["docker", "run", "-d", "--name", "ntfy", "--network", "uk", "binwiederhier/ntfy", "serve"])
    t0 = time.time()
    sh(["docker", "run", "-d", "--name", "kuma", "--network", "uk", "-p", "3001:3001",
        "-e", "UPTIME_KUMA_DB_TYPE=sqlite", KUMA])
    for _ in range(90):
        if "Listening on" in sh(["docker", "logs", "kuma"]):
            break
        time.sleep(1)
    anota("arranque", f"docker run -d --name kuma -p 3001:3001 {KUMA}",
          "\n".join(linea for linea in sh(["docker", "logs", "kuma"]).splitlines()
                    if "Version" in linea or "need setup" in linea or "localhost" in linea)
          + f"\n(listo en {time.time() - t0:.0f} s)")
    anota("tamaño de la imagen", f"docker image inspect {KUMA}",
          f"{int(sh(['docker', 'image', 'inspect', KUMA, '--format', '{{.Size}}'])) / 1e6:.0f} MB")
    captura("01-setup")

    salida.append("\n## 2 · Cuenta, notificación a ntfy y tres monitores")
    anota("configurar por socket.io", "python cliente.py setup", cliente("setup"))

    salida.append("\n## 3 · Todo arriba")
    time.sleep(50)
    anota("latidos", "SELECT ... FROM heartbeat (kuma.db)", latidos())
    anota("uso de memoria", "docker stats --no-stream kuma",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}} {{.CPUPerc}}", "kuma"]))
    captura("02-todo-arriba")
    captura("03-detalle-web", "/dashboard/1")

    salida.append("\n## 4 · Se cae la web")
    t_caida = datetime.now(timezone.utc)
    sh(["docker", "stop", "web"])
    anota("parar la web", "docker stop web", f"parada a las {t_caida:%H:%M:%S} UTC")
    time.sleep(50)
    anota("latidos", "SELECT ... FROM heartbeat (kuma.db)", latidos())
    anota("alertas recibidas en ntfy", "curl ntfy/alertas/json?poll=1", ntfy())
    captura("04-caida")
    captura("05-detalle-caida", "/dashboard/1")

    salida.append("\n## 5 · Vuelve la web")
    sh(["docker", "start", "web"])
    time.sleep(50)
    anota("latidos", "SELECT ... FROM heartbeat (kuma.db)", latidos())
    anota("alertas recibidas en ntfy", "curl ntfy/alertas/json?poll=1", ntfy())
    captura("06-recuperado")

    sh(["docker", "rm", "-f", "kuma", "web", "redis", "ntfy"])
    sh(["docker", "network", "rm", "uk"])
    cab = ["# SALIDA — Uptime Kuma (vídeo 326)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Imagen {KUMA}. Intervalo de los monitores: 20 s, sin reintentos."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
