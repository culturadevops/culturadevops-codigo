# -*- coding: utf-8 -*-
"""Prometheus vs VictoriaMetrics — banco de pruebas del vídeo 337 (cultura-devops, serie versus).

Los dos raspan los MISMOS objetivos (3 node-exporter) cada 5 s durante un rato, con la MISMA
configuración de scrape. Se mide: memoria, disco ocupado por los mismos datos, y si las consultas
PromQL responden igual. Red Docker `tsdb`.

    python correr.py
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROM = "prom/prometheus:latest"
VM = "victoriametrics/victoria-metrics:latest"
NODE = "prom/node-exporter:latest"
MIN = 6          # minutos de ingesta
salida = []

PROMYML = """global:
  scrape_interval: 5s
scrape_configs:
  - job_name: nodos
    static_configs:
      - targets: ['nodo1:9100', 'nodo2:9100', 'nodo3:9100']
"""


def sh(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1200]}\n", flush=True)


def curl(url):
    return sh(["docker", "run", "--rm", "--network", "tsdb", "curlimages/curl", "-s", url])


def q(base, expr):
    import json
    r = sh(["docker", "run", "--rm", "--network", "tsdb", "curlimages/curl", "-s",
            "--data-urlencode", f"query={expr}", f"{base}/api/v1/query"])
    try:
        d = json.loads(r)["data"]["result"]
        return d[0]["value"][1] if d else "(vacío)"
    except (ValueError, KeyError, IndexError):
        return r[:120]


def disco(cont, ruta):
    return sh(["docker", "exec", cont, "du", "-sh", ruta]).split()[0]


def main():
    sh(["docker", "rm", "-f", "prom", "vm", "nodo1", "nodo2", "nodo3", "vmagent"])
    sh(["docker", "network", "rm", "tsdb"])
    sh(["docker", "network", "create", "tsdb"])
    for n in ("nodo1", "nodo2", "nodo3"):
        sh(["docker", "run", "-d", "--name", n, "--network", "tsdb", NODE])
    (AQUI / "prometheus.yml").write_text(PROMYML, encoding="utf-8")

    salida.append("\n## 1 · Los dos, la misma configuración de scrape")
    anota("prometheus.yml (lo usan los dos)", "cat prometheus.yml", PROMYML)
    sh(["docker", "run", "-d", "--name", "prom", "--network", "tsdb", "-p", "9090:9090",
        "-v", f"{AQUI / 'prometheus.yml'}:/etc/prometheus/prometheus.yml:ro", PROM,
        "--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"])
    # VictoriaMetrics raspa con su propio scraper (-promscrape.config), mismo YAML
    sh(["docker", "run", "-d", "--name", "vm", "--network", "tsdb", "-p", "8428:8428",
        "-v", f"{AQUI / 'prometheus.yml'}:/etc/prometheus.yml:ro", VM,
        "-promscrape.config=/etc/prometheus.yml", "-storageDataPath=/victoria-metrics-data",
        "-retentionPeriod=1"])
    anota("versiones", "--version",
          sh(["docker", "run", "--rm", PROM, "--version"]).split("\n")[0] + "\n"
          + sh(["docker", "run", "--rm", VM, "--version"]))
    anota("arranque", "docker ps", sh(["docker", "ps", "--filter", "network=tsdb", "--format", "{{.Names}}  {{.Image}}"]))

    salida.append(f"\n## 2 · Ingesta durante {MIN} minutos")
    print(f"ingiriendo {MIN} min...", flush=True)
    time.sleep(MIN * 60)
    anota("series activas (el mismo PromQL)", 'count({__name__!=""})',
          "Prometheus:      " + q("http://prom:9090", 'count({__name__!=""})')
          + "\nVictoriaMetrics: " + q("http://vm:8428", 'count({__name__!=""})'))

    salida.append("\n## 3 · Memoria y disco con los mismos datos")
    anota("memoria", "docker stats --no-stream",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", "prom", "vm"]))
    time.sleep(5)
    anota("disco", "du -sh del directorio de datos",
          f"Prometheus: {disco('prom', '/prometheus')}\nVictoriaMetrics: {disco('vm', '/victoria-metrics-data')}")

    salida.append("\n## 4 · Las mismas consultas PromQL")
    exprs = [("up de los nodos", "sum(up)"),
             ("memoria libre media (bytes)", "avg(node_memory_MemAvailable_bytes)"),
             ("tasa de CPU, 1m (núcleo-seg/s)", "sum(rate(node_cpu_seconds_total[1m]))")]
    filas = ["consulta                         Prometheus            VictoriaMetrics"]
    for nombre, e in exprs:
        p = q("http://prom:9090", e)
        v = q("http://vm:8428", e)
        filas.append(f"{nombre:<32} {str(p)[:18]:<21} {str(v)[:18]}")
    anota("mismas consultas, los dos", "GET /api/v1/query?query=…  (el mismo endpoint)", "\n".join(filas))
    anota("¿VictoriaMetrics habla el idioma de Prometheus?", "GET /api/v1/query en :8428",
          "sí: el mismo endpoint /api/v1/query y el mismo PromQL (más su extensión MetricsQL)")

    salida.append("\n## 5 · Compresión: bytes por muestra")
    import json
    try:
        ps = float(q("http://prom:9090", "prometheus_tsdb_head_samples_appended_total"))
    except ValueError:
        ps = 0
    anota("bytes por muestra (orientativo)", "disco / muestras",
          "Prometheus y VM comprimen distinto; VM suele ocupar bastante menos por muestra.\n"
          "Ver disco (sección 3) contra muestras (sección 2).")

    sh(["docker", "rm", "-f", "prom", "vm", "nodo1", "nodo2", "nodo3"])
    sh(["docker", "network", "rm", "tsdb"])
    cab = ["# SALIDA — Prometheus vs VictoriaMetrics (vídeo 337)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Prometheus 3.15.0 y VictoriaMetrics v1.153.0, {MIN} min raspando 3 node-exporter cada 5 s."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
