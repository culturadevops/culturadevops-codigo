# -*- coding: utf-8 -*-
"""Demo de «Prometheus y Grafana en 5 minutos» (cultura-devops). Todo en Docker, red propia p5min:
  · Prometheus raspa tres objetivos: a sí mismo, a Grafana y a un servicio que NO existe («pagos»);
  · consulta PromQL `up` por la API;
  · una regla de alerta («ServicioCaido», up == 0 durante 20 s) que pasa de pending a firing, con el tiempo medido;
  · Grafana con la fuente de datos aprovisionada por archivo, y la misma consulta hecha A TRAVÉS de Grafana.
Credenciales: las de fábrica de Grafana (admin/admin) en un contenedor local que se borra al terminar.
    python correr.py   -> SALIDA.md
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
PROM, GRAF = "prom/prometheus:v3.15.1", "grafana/grafana:13.2.4"
OUT = []

PROM_YML = """global:
  scrape_interval: 5s
  evaluation_interval: 5s
rule_files: [/etc/prometheus/reglas.yml]
scrape_configs:
  - job_name: prometheus
    static_configs: [{targets: ["localhost:9090"]}]
  - job_name: grafana
    static_configs: [{targets: ["grafana:3000"]}]
  - job_name: pagos
    static_configs: [{targets: ["pagos:8080"]}]
"""
REGLAS = """groups:
  - name: basicas
    rules:
      - alert: ServicioCaido
        expr: up == 0
        for: 20s
        labels: {severidad: critica}
        annotations: {resumen: "{{ $labels.job }} no responde"}
"""
DS = """apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    uid: prom
    url: http://prometheus:9090
    access: proxy
    isDefault: true
"""


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "cliente5", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def limpiar():
    for c in ("prometheus", "grafana", "cliente5"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", "p5min"])


def main():
    limpiar()
    conf = AQUI / "_conf"
    (conf / "ds").mkdir(parents=True, exist_ok=True)
    (conf / "prometheus.yml").write_text(PROM_YML, encoding="utf-8", newline="\n")
    (conf / "reglas.yml").write_text(REGLAS, encoding="utf-8", newline="\n")
    (conf / "ds" / "prometheus.yml").write_text(DS, encoding="utf-8", newline="\n")
    w = str(conf).replace("\\", "/")
    run(["docker", "network", "create", "p5min"])
    t0 = time.time()
    run(["docker", "run", "-d", "--name", "prometheus", "--network", "p5min",
         "-v", f"{w}/prometheus.yml:/etc/prometheus/prometheus.yml", "-v", f"{w}/reglas.yml:/etc/prometheus/reglas.yml", PROM])
    run(["docker", "run", "-d", "--name", "grafana", "--network", "p5min",
         "-v", f"{w}/ds:/etc/grafana/provisioning/datasources", GRAF])
    run(["docker", "run", "-d", "--name", "cliente5", "--network", "p5min", "alpine:3.22", "sleep", "infinity"])
    ex("apk add -q curl jq >/dev/null")

    OUT.append(f"# SALIDA — Prometheus y Grafana en 5 minutos (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
               f"con `python correr.py`. Imágenes `{PROM}` y `{GRAF}`; red de Docker propia; cliente curl+jq en Alpine.\n")
    OUT.append("## 1 · La configuración\n")
    OUT.append("### prometheus.yml\n\n```\n" + PROM_YML + "```\n")
    OUT.append("### reglas.yml\n\n```\n" + REGLAS + "```\n")

    # esperar a que Prometheus haya raspado los 3 objetivos al menos una vez
    for _ in range(60):
        s, _ = ex("curl -s http://prometheus:9090/api/v1/targets | jq '[.data.activeTargets[] | select(.lastScrape != \"0001-01-01T00:00:00Z\")] | length'")
        if s.strip() == "3":
            break
        time.sleep(2)

    OUT.append("## 2 · Los objetivos\n")
    bloque("¿quién responde?", "curl -s prometheus:9090/api/v1/targets | jq …",
           "curl -s http://prometheus:9090/api/v1/targets | jq -r '.data.activeTargets[] | \"\\(.labels.job)\\t\\(.health)\\t\\(.lastError)\"'")
    bloque("PromQL: up", "curl -s 'prometheus:9090/api/v1/query?query=up' | jq …",
           "curl -s 'http://prometheus:9090/api/v1/query?query=up' | jq -r '.data.result[] | \"up{job=\\\"\\(.metric.job)\\\"} = \\(.value[1])\"' | sort")

    OUT.append("## 3 · La alerta\n")
    estados, visto = [], set()
    t_alerta0 = time.time()
    for _ in range(120):
        s, _ = ex("curl -s http://prometheus:9090/api/v1/alerts | jq -r '.data.alerts[] | \"\\(.labels.alertname) \\(.labels.job) \\(.state)\"'")
        st = s.strip()
        if st and st not in visto:
            visto.add(st)
            estados.append(f"t+{time.time() - t0:5.1f}s desde el arranque · {st}")
        if "firing" in st:
            break
        time.sleep(1)
    OUT.append("### pending → firing (sondeando /api/v1/alerts cada segundo)\n\n`$ curl -s prometheus:9090/api/v1/alerts | jq …`\n\n```\n"
               + "\n".join(estados) + "\n```\n")
    print("[ok] alerta", estados)

    OUT.append("## 4 · Grafana\n")
    for _ in range(60):
        s, _ = ex("curl -s http://grafana:3000/api/health | jq -r .database")
        if s.strip() == "ok":
            break
        time.sleep(2)
    bloque("salud", "curl -s grafana:3000/api/health", "curl -s http://grafana:3000/api/health | jq -c '{database, version}'")
    bloque("la fuente de datos (aprovisionada por archivo)", "curl -s -u admin:admin grafana:3000/api/datasources | jq …",
           "curl -s -u admin:admin http://grafana:3000/api/datasources | jq -r '.[] | \"\\(.name)\\t\\(.type)\\t\\(.url)\"'")
    q = json.dumps({"queries": [{"refId": "A", "datasource": {"uid": "prom"}, "expr": "up", "instant": True}],
                    "from": "now-5m", "to": "now"})
    bloque("la misma consulta, a través de Grafana", "curl -s -u admin:admin -X POST grafana:3000/api/ds/query -d '{…expr: up…}' | jq …",
           f"curl -s -u admin:admin -H 'Content-Type: application/json' -X POST http://grafana:3000/api/ds/query -d '{q}' | "
           "jq -r '.results.A.frames[] | \"\\(.schema.fields[1].labels.job) = \\(.data.values[1][0])\"' | sort")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    limpiar()
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
