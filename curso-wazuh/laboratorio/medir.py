# -*- coding: utf-8 -*-
"""medir.py — saca las cifras del laboratorio. Es la fuente de TODO número del curso.

El canon prohíbe citar cifras de memoria o de la documentación: lo que el curso afirme sobre
versiones, RAM, arranque o disco tiene que salir de ejecutar esto. Escribe `MEDIDO.md` con la
fecha, para que dentro de tres meses se sepa cuándo se midió y con qué versión.

    python medir.py            mide y escribe MEDIDO.md
    python medir.py --ver      solo lo enseña por pantalla
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CONT = ["lab-wazuh-indexer", "lab-wazuh-manager", "lab-wazuh-dashboard", "lab-wazuh-victima"]


def sh(*args, t=60):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=t)
    return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode


def estado():
    out, _, _ = sh("docker", "ps", "-a", "--filter", "name=lab-wazuh",
                   "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}")
    filas = []
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) == 3:
            filas.append({"nombre": p[0], "estado": p[1], "imagen": p[2]})
    return filas


def recursos():
    """RAM y CPU reales de cada contenedor. `stats --no-stream` da una foto."""
    out, _, _ = sh("docker", "stats", "--no-stream", "--format",
                   "{{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}", t=90)
    filas = []
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) == 4 and p[0].startswith("lab-wazuh"):
            filas.append({"nombre": p[0], "ram": p[1], "ram_pct": p[2], "cpu": p[3]})
    return filas


def version_wazuh():
    """La versión que dice el manager, no la etiqueta de la imagen: pueden no coincidir."""
    out, err, rc = sh("docker", "exec", "lab-wazuh-manager",
                      "/var/ossec/bin/wazuh-control", "info")
    return out or err or f"(rc={rc})"


def agentes():
    out, err, rc = sh("docker", "exec", "lab-wazuh-manager", "/var/ossec/bin/agent_control", "-l")
    return out or err or f"(rc={rc})"


def indices():
    """Cuánto ocupa lo guardado. De aquí sale la cifra de «disco por día»."""
    # ⚠️ http:// y sin usuario NO sirve: el indexer habla HTTPS y pide credenciales. Escrito así,
    # esto devolvía siempre «no responde» y **tapó durante cuatro días** que el manager no podía
    # escribir en el indexer (401). Un medidor que falla en silencio es peor que no medir.
    out, err, cod = sh("docker", "exec", "lab-wazuh-indexer", "curl", "-sk",
                       "-u", "admin:SecretPassword",
                       "https://localhost:9200/_cat/indices?v&h=index,docs.count,store.size")
    if not out:
        return "⛔ el indexer no contestó (curl %d): %s" % (cod, (err or "sin detalle")[:120])
    return out


def alertas():
    """Cuántas alertas hay ahora mismo, sin haber hecho nada: la línea base del ruido."""
    out, _, _ = sh("docker", "exec", "lab-wazuh-manager", "sh", "-c",
                   "wc -l < /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 0")
    return out.strip() or "0"


def disco_imagenes():
    out, _, _ = sh("docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}")
    return [l for l in out.splitlines() if "wazuh" in l.lower()]


def main():
    t = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    d = {
        "medido": t,
        "contenedores": estado(),
        "recursos": recursos(),
        "version": version_wazuh(),
        "agentes": agentes(),
        "indices": indices(),
        "alertas_hasta_ahora": alertas(),
        "imagenes": disco_imagenes(),
    }
    if "--ver" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return

    L = [f"# Medido en el laboratorio · {t}", "",
         "⚠️ Generado por `medir.py`. **No editar a mano**: si un número de aquí no cuadra, se",
         "vuelve a medir. Es la única fuente de cifras del curso.", "", "## Contenedores", ""]
    for c in d["contenedores"]:
        L.append(f"- `{c['nombre']}` · {c['estado']} · imagen `{c['imagen']}`")
    L += ["", "## RAM y CPU (foto puntual)", "",
          "| contenedor | RAM | % | CPU |", "|---|---|---|---|"]
    for c in d["recursos"]:
        L.append(f"| `{c['nombre']}` | {c['ram']} | {c['ram_pct']} | {c['cpu']} |")
    L += ["", "## Versión que dice el manager", "", "```", d["version"], "```",
          "", "## Agentes", "", "```", d["agentes"], "```",
          "", "## Índices y lo que ocupan", "", "```", d["indices"], "```",
          "", f"## Alertas acumuladas hasta ahora: **{d['alertas_hasta_ahora']}**", "",
          "Sin haber atacado nada. Es la línea base del ruido, y es el dato de la lección 05.",
          "", "## Lo que ocupan las imágenes", "", "```"] + d["imagenes"] + ["```"]
    (AQUI / "MEDIDO.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[ok] MEDIDO.md · {len(d['contenedores'])} contenedores · "
          f"{d['alertas_hasta_ahora']} alertas de base")


if __name__ == "__main__":
    main()
