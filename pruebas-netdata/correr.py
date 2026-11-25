# -*- coding: utf-8 -*-
"""Netdata — banco de pruebas del vídeo 334 (cultura-devops, serie herramientas).

netdata/netdata:stable con el docker run oficial (pid=host, /proc, /sys, docker.sock), un ntfy
propio para las alertas, y carga de CPU con contenedores en bucle. ⛔ Correr SIN renders ni otros
bancos a la vez: la CPU de la máquina es lo que se mide.

    python correr.py
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\netdata")
IMG = "netdata/netdata:stable"
salida = []

ALERTA = """ alarm: cpu_30s_demo
    on: system.cpu
lookup: average -30s unaligned of user,system,softirq,irq,guest
 units: %
 every: 10s
  warn: $this > 50
  crit: $this > 80
  info: CPU media de los últimos 30 segundos (alerta de prueba)
    to: sysadmin
"""


def sh(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def api(ruta):
    return sh(["curl", "-s", f"http://localhost:19999{ruta}"])


def captura(nombre, ruta="/", clic=None):
    # 2026-10-12: Netdata 2.12 ya no sirve /v1/ ni /v2/ («File does not exist»): el panel está en la raíz.
    PUB.mkdir(parents=True, exist_ok=True)
    print(sh(["node", str(AQUI / "capturar.js"), str(PUB / f"{nombre}.png"), ruta] + ([clic] if clic else [])))


def alarmas():
    d = json.loads(api("/api/v1/alarms?active") or "{}")
    return "\n".join(f"{a['name']:<28} {a['status']:<9} {a.get('value_string', '')}  {a['chart']}"
                     for a in d.get("alarms", {}).values()) or "(ninguna activa)"


def cpu_media(seg=30):
    d = json.loads(api(f"/api/v1/data?chart=system.cpu&after=-{seg}&points=1&group=average&format=json&options=jsonwrap") or "{}")
    try:
        fila = d["result"]["data"][0]
        return f"{sum(v for v in fila[1:] if v):.1f} %"
    except (KeyError, IndexError, TypeError):
        return "?"


def main():
    sh(["docker", "rm", "-f", "netdata", "ntfy", *[f"carga{i}" for i in range(16)]])
    sh(["docker", "network", "rm", "nd"])
    sh(["docker", "network", "create", "nd"])
    sh(["docker", "run", "-d", "--name", "ntfy", "--network", "nd", "-p", "8099:80", "binwiederhier/ntfy", "serve"])
    (AQUI / "cpu_demo.conf").write_text(ALERTA, encoding="utf-8")

    salida.append("\n## 1 · Instalar: el docker run oficial")
    t0 = time.time()
    sh(["docker", "run", "-d", "--name", "netdata", "--pid=host", "--network", "nd", "-p", "19999:19999",
        "--cap-add", "SYS_PTRACE", "--cap-add", "SYS_ADMIN", "--security-opt", "apparmor=unconfined",
        "-v", "/proc:/host/proc:ro", "-v", "/sys:/host/sys:ro", "-v", "/etc/os-release:/host/etc/os-release:ro",
        "-v", "//var/run/docker.sock:/var/run/docker.sock:ro",
        "-v", f"{AQUI / 'cpu_demo.conf'}:/etc/netdata/health.d/cpu_demo.conf:ro",
        "-e", "DEFAULT_RECIPIENT_NTFY=http://ntfy/alertas", IMG])
    for _ in range(90):
        if '"version"' in api("/api/v1/info"):
            break
        time.sleep(1)
    anota("arranque", f"docker run -d --name netdata ... {IMG}", f"API respondiendo en {time.time() - t0:.0f} s")
    sh(["docker", "exec", "netdata", "sh", "-c",
        "sed -i 's|^DEFAULT_RECIPIENT_NTFY=.*|DEFAULT_RECIPIENT_NTFY=\"http://ntfy/alertas\"|' /usr/lib/netdata/conf.d/health_alarm_notify.conf"])
    time.sleep(60)
    info = json.loads(api("/api/v1/info"))
    anota("versión y sistema", "curl /api/v1/info",
          json.dumps({k: info.get(k) for k in ("version", "os_name", "os_version", "kernel_version",
                                                 "cores_total", "total_disk_space", "ram_total")}, ensure_ascii=False, indent=1))
    charts = json.loads(api("/api/v1/charts"))["charts"]
    familias = {}
    for c in charts.values():
        familias[c["type"].split(".")[0].split("_")[0]] = familias.get(c["type"].split(".")[0].split("_")[0], 0) + 1
    top = sorted(familias.items(), key=lambda kv: -kv[1])[:12]
    dims = sum(len(c.get("dimensions", {})) for c in charts.values())
    anota("lo que mide sin configurar nada", "curl /api/v1/charts",
          f"{len(charts)} gráficas, {dims} métricas (dimensiones)\n" + "\n".join(f"{k:<20} {v}" for k, v in top))
    anota("frecuencia", "update_every de system.cpu", str(charts.get("system.cpu", {}).get("update_every")) + " s")
    anota("memoria y CPU de netdata", "docker stats --no-stream netdata",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}} {{.CPUPerc}}", "netdata"]))
    anota("alertas cargadas", "curl /api/v1/alarms?all | contar",
          f"{len(json.loads(api('/api/v1/alarms?all'))['alarms'])} alertas configuradas de serie (+ la mía)")
    anota("la alerta por defecto de CPU", "health.d/cpu.conf (10min_cpu_usage)",
          sh(["docker", "exec", "netdata", "sh", "-c", "sed -n '4,18p' /usr/lib/netdata/conf.d/health.d/cpu.conf"]))
    anota("mi alerta de prueba", "cat health.d/cpu_demo.conf", ALERTA)
    anota("estado en reposo", "CPU media 30 s; alertas activas", f"CPU {cpu_media()}\n{alarmas()}")
    captura("01-panel")
    captura("02-alertas-reposo", "/", "Alerts")

    salida.append("\n## 2 · Carga de CPU")
    nucleos = info.get("cores_total") or "8"
    n = int(nucleos)
    t_carga = datetime.now(timezone.utc)
    for i in range(n):
        sh(["docker", "run", "-d", "--rm", "--name", f"carga{i}", "alpine", "sh", "-c", "while :; do :; done"])
    anota("lanzar la carga", f"{n} contenedores con un bucle infinito (uno por núcleo)",
          f"lanzados a las {t_carga:%H:%M:%S} UTC")
    estados = []
    t = time.time()
    while time.time() - t < 150:
        estados.append(f"t={time.time() - t:4.0f}s  CPU(30s)={cpu_media()}  " + alarmas().replace("\n", " | "))
        if "CRITICAL" in estados[-1] and time.time() - t > 60:
            break
        time.sleep(10)
    anota("cada 10 s", "CPU media 30 s y alertas activas", "\n".join(estados))
    # capturas con la CPU AÚN alta (Playwright sí funciona; docker exec no)
    captura("03-cpu-carga")
    captura("04-alertas", "/", "Alerts")

    salida.append("\n## 3 · Lo que llegó a ntfy")
    time.sleep(8)
    raw = sh(["docker", "run", "--rm", "--network", "nd", "curlimages/curl", "-s", "http://ntfy/alertas/json?poll=1"], timeout=60)
    msgs = []
    for linea in raw.splitlines():
        try:
            d = json.loads(linea)
            msgs.append(f"{datetime.fromtimestamp(d['time'], timezone.utc):%H:%M:%S}  prio={d.get('priority', 3)}  "
                        f"{d.get('title', '')} | {d.get('message', '')[:100]}")
        except ValueError:
            pass
    anota("alertas en ntfy", "curl ntfy/alertas/json?poll=1", "\n".join(msgs) or "(sin mensajes)")

    salida.append("\n## 4 · Quitar la carga y recuperarse")
    try:
        sh(["docker", "rm", "-f", *[f"carga{i}" for i in range(n)]], timeout=120)
    except Exception:
        pass
    t = time.time()
    estados = []
    while time.time() - t < 150:
        estados.append(f"t={time.time() - t:4.0f}s  CPU(30s)={cpu_media()}  " + alarmas().replace("\n", " | "))
        if "cpu_30s_demo" not in estados[-1] and time.time() - t > 30:
            break
        time.sleep(10)
    anota("cada 10 s", "CPU media 30 s y alertas activas", "\n".join(estados))
    captura("05-recuperado")

    salida.append("\n## 5 · El registro de alertas (CPU ya baja)")
    # 2026-10-12: el `docker exec` a health.log se colgó 900 s en la corrida anterior; el historial sale de la API.
    try:
        reg = json.loads(api("/api/v1/alarm_log") or "[]")
    except ValueError:
        reg = []
    filas = [f"{datetime.fromtimestamp(e['when'], timezone.utc):%H:%M:%S}  {e.get('old_status', '?'):>8} → {e.get('status', '?'):<8} "
             f"{e.get('value_string', '')}" for e in sorted(reg, key=lambda e: e.get("when", 0)) if e.get("name") == "cpu_30s_demo"]
    anota("/api/v1/alarm_log de cpu_30s_demo", "el ciclo WARNING → CRITICAL → CLEAR", "\n".join(filas[-8:]) or "(vacío)")

    sh(["docker", "rm", "-f", "netdata", "ntfy"])
    sh(["docker", "network", "rm", "nd"])
    cab = ["# SALIDA — Netdata (vídeo 334)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Imagen {IMG}; mide la VM de Docker Desktop (Linux) donde corren los contenedores."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
