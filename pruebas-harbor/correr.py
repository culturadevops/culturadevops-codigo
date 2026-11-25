# -*- coding: utf-8 -*-
"""Harbor — banco de pruebas del vídeo 331 (cultura-devops, serie herramientas).

Harbor v2.15.3 (instalador online + Trivy) DENTRO de un docker:dind, para no tocar el Docker del
anfitrión. Hostname harbor.local → 127.0.0.1 dentro del dind; el dind confía en él por HTTP
(--insecure-registry). El panel se publica en http://localhost:8088.

Se mide: instalación, proyecto con escaneo al subir, push de una imagen vieja y una nueva,
vulnerabilidades encontradas, la política que impide descargar imágenes vulnerables, y la
retención de etiquetas (dry run y de verdad).

    python correr.py
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\harbor")
VER = "v2.15.3"
D = "harbor-dind"
CLAVE = "Harbor-de-prueba-123"
API = "http://harbor.local/api/v2.0"
salida = []


def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return (r.stdout + r.stderr).strip()


def x(script, timeout=1800):
    return sh(["docker", "exec", D, "sh", "-c", script], timeout=timeout)


def api(metodo, ruta, datos=None):
    d = f"-H 'Content-Type: application/json' -d '{json.dumps(datos)}'" if datos is not None else ""
    return x(f"curl -s -u admin:{CLAVE} -X {metodo} {d} '{API}{ruta}'")


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def captura(nombre, ruta):
    PUB.mkdir(parents=True, exist_ok=True)
    print(sh(["node", str(AQUI / "capturar.js"), str(PUB / f"{nombre}.png"), ruta, CLAVE]))


def espera_escaneo(repo, tag, max_s=600):
    t = time.time()
    while time.time() - t < max_s:
        r = api("GET", f"/projects/demo/repositories/{repo}/artifacts/{tag}?with_scan_overview=true")
        try:
            so = json.loads(r).get("scan_overview") or {}
            v = next(iter(so.values()), {})
            if v.get("scan_status") == "Success":
                return v, time.time() - t
        except (ValueError, StopIteration):
            pass
        time.sleep(5)
    return None, None


def main():
    sh(["docker", "rm", "-f", D])
    sh(["docker", "volume", "rm", "-f", "harbor-dind-data"])
    sh(["docker", "run", "-d", "--privileged", "--name", D, "-p", "8088:80",
        "-v", "harbor-dind-data:/var/lib/docker", "docker:dind",
        "--insecure-registry", "harbor.local"])
    for _ in range(60):
        if "Server Version" in x("docker info 2>/dev/null | grep 'Server Version'"):
            break
        time.sleep(2)
    x("echo '127.0.0.1 harbor.local' >> /etc/hosts && apk add --no-cache curl jq bash >/dev/null")

    salida.append("\n## 1 · Instalar Harbor (instalador online + Trivy)")
    x(f"cd /opt && wget -q https://github.com/goharbor/harbor/releases/download/{VER}/"
      f"harbor-online-installer-{VER}.tgz && tar xzf harbor-online-installer-{VER}.tgz")
    x("cd /opt/harbor && cp harbor.yml.tmpl harbor.yml && "
      "sed -i 's/^hostname: .*/hostname: harbor.local/' harbor.yml && "
      f"sed -i 's/^harbor_admin_password: .*/harbor_admin_password: {CLAVE}/' harbor.yml && "
      "sed -i '/^https:/,/private_key:/ s/^/#/' harbor.yml")
    anota("harbor.yml (lo que cambié)", "grep -E '^(hostname|harbor_admin_password|#https|http:)' harbor.yml",
          x("cd /opt/harbor && grep -nE '^(hostname|harbor_admin_password|#https|http:|  port: 80|data_volume)' harbor.yml"))
    t0 = time.time()
    r = x("cd /opt/harbor && ./install.sh --with-trivy 2>&1", timeout=3600)
    anota("install.sh --with-trivy", "./install.sh --with-trivy",
          "\n".join(l for l in r.splitlines() if l.startswith("[Step") or "successfully" in l
                    or "Creating" in l or "Started" in l)[-3000:] + f"\n(instalado en {time.time() - t0:.0f} s)")
    for _ in range(120):
        if '"status":"healthy"' in x(f"curl -s {API}/health"):
            break
        time.sleep(3)
    anota("contenedores", "docker ps --format '{{.Names}}  {{.Image}}'",
          x("docker ps --format '{{.Names}}  {{.Image}}' | sort"))
    anota("salud", "curl /api/v2.0/health", x(f"curl -s {API}/health | jq -c '.components[] | [.name,.status]'"))
    anota("memoria", "docker stats --no-stream",
          x("docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | sort"))
    anota("versión", "curl /api/v2.0/systeminfo", x(f"curl -s -u admin:{CLAVE} {API}/systeminfo | jq -r .harbor_version"))

    salida.append("\n## 2 · Un proyecto que escanea al subir")
    anota("crear proyecto", "POST /projects {name: demo, auto_scan: true}",
          api("POST", "/projects", {"project_name": "demo", "metadata": {"auto_scan": "true", "public": "false"}})
          + "\n" + x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo' | jq -c '{{name, metadata}}'"))

    salida.append("\n## 3 · Subir una imagen vieja y una nueva")
    x(f"echo {CLAVE} | docker login harbor.local -u admin --password-stdin")
    for img, tag in (("nginx:1.20", "nginx:1.20"), ("alpine:3.22", "alpine:3.22")):
        t = time.time()
        r = x(f"docker pull -q {img} && docker tag {img} harbor.local/demo/{tag} && docker push harbor.local/demo/{tag} 2>&1 | tail -2")
        anota(f"push {tag}", f"docker push harbor.local/demo/{tag}", r + f"\n({time.time() - t:.0f} s)")
    for repo, tag in (("nginx", "1.20"), ("alpine", "3.22")):
        v, s = espera_escaneo(repo, tag)
        if v:
            res = v.get("summary", {})
            anota(f"escaneo de {repo}:{tag}", f"GET .../repositories/{repo}/artifacts/{tag}?with_scan_overview=true",
                  json.dumps({"scanner": v.get("scanner", {}).get("name"), "severidad_max": v.get("severity"),
                              "total": res.get("total"), "por_severidad": res.get("summary")}, ensure_ascii=False)
                  + f"\n(resultado {s:.0f} s después de pedirlo)")
    anota("las 5 más graves de nginx:1.20", "GET .../vulnerabilities",
          x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo/repositories/nginx/artifacts/1.20/additions/vulnerabilities' "
            "| jq -r '.[].vulnerabilities | sort_by(.severity) | map(select(.severity==\"Critical\")) | .[0:5][] | "
            "\"\\(.id)  \\(.package) \\(.version)  \\(.severity)\"'"))
    captura("01-proyecto", "/harbor/projects")
    captura("02-escaneo", "/harbor/projects/2/repositories/nginx/artifacts-tab")

    salida.append("\n## 4 · Impedir descargar imágenes vulnerables")
    anota("activar la política", "PUT /projects/demo {prevent_vul: true, severity: high}",
          api("PUT", "/projects/demo", {"metadata": {"prevent_vul": "true", "severity": "high"}}) or "(200, sin cuerpo)")
    anota("pull de nginx:1.20", "docker pull harbor.local/demo/nginx:1.20",
          x("docker rmi -f harbor.local/demo/nginx:1.20 >/dev/null; docker pull harbor.local/demo/nginx:1.20 2>&1; echo codigo=$?"))
    anota("pull de alpine:3.22", "docker pull harbor.local/demo/alpine:3.22",
          x("docker rmi -f harbor.local/demo/alpine:3.22 >/dev/null; docker pull -q harbor.local/demo/alpine:3.22 2>&1; echo codigo=$?"))

    salida.append("\n## 5 · Retención: quedarse con las 2 últimas etiquetas")
    for i in range(1, 6):
        x(f"docker tag alpine:3.22 harbor.local/demo/app:v{i} && echo v{i} > /tmp/v && "
          f"printf 'FROM alpine:3.22\\nRUN echo v{i} > /v\\n' | docker build -q -t harbor.local/demo/app:v{i} - >/dev/null && "
          f"docker push -q harbor.local/demo/app:v{i}")
        time.sleep(2)
    anota("etiquetas de app", "GET .../repositories/app/artifacts",
          x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo/repositories/app/artifacts?page_size=20' | jq -r '.[].tags[].name' | sort"))
    pid = x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo' | jq -r .project_id")
    politica = {"algorithm": "or", "scope": {"level": "project", "ref": int(pid)},
                "trigger": {"kind": "Schedule", "settings": {"cron": ""}},
                "rules": [{"action": "retain", "template": "latestPushedK", "params": {"latestPushedK": 2},
                           "tag_selectors": [{"kind": "doublestar", "decoration": "matches", "pattern": "**"}],
                           "scope_selectors": {"repository": [{"kind": "doublestar", "decoration": "repoMatches", "pattern": "app"}]}}]}
    anota("crear la regla", "POST /retentions (retener las 2 últimas subidas de app)",
          api("POST", "/retentions", politica) or "(201)")
    rid = x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo/metadatas/retention_id' | jq -r .retention_id")
    api("POST", f"/retentions/{rid}/executions", {"dry_run": True})
    time.sleep(20)
    ej = x(f"curl -s -u admin:{CLAVE} '{API}/retentions/{rid}/executions' | jq -c '.[0] | {{id, dry_run, status}}'")
    eid = json.loads(ej)["id"]
    anota("ensayo (dry run)", "POST /retentions/{id}/executions {dry_run: true}",
          ej + "\n" + x(f"curl -s -u admin:{CLAVE} '{API}/retentions/{rid}/executions/{eid}/tasks' | jq -c '.[] | {{repository, retained, total, status}}'"))
    anota("después del ensayo", "etiquetas de app",
          x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo/repositories/app/artifacts?page_size=20' | jq -r '.[].tags[].name' | sort"))
    api("POST", f"/retentions/{rid}/executions", {"dry_run": False})
    time.sleep(25)
    anota("de verdad", "POST /retentions/{id}/executions {dry_run: false}",
          x(f"curl -s -u admin:{CLAVE} '{API}/retentions/{rid}/executions' | jq -c '.[0] | {{id, dry_run, status}}'"))
    anota("etiquetas que quedan", "etiquetas de app",
          x(f"curl -s -u admin:{CLAVE} '{API}/projects/demo/repositories/app/artifacts?page_size=20' | jq -r '.[].tags[].name' | sort"))
    captura("03-retencion", f"/harbor/projects/{pid}/tag-retention")
    anota("¿y el disco?", "du -sh /data/registry (antes de la recolección de basura)",
          x("du -sh /data/registry 2>/dev/null"))
    api("POST", "/system/gc/schedule", {"schedule": {"type": "Manual"}, "parameters": {"delete_untagged": True}})
    time.sleep(30)
    anota("recolección de basura", "POST /system/gc/schedule (manual)",
          x(f"curl -s -u admin:{CLAVE} '{API}/system/gc?page_size=1' | jq -c '.[0] | {{job_status, job_parameters}}'")
          + "\n" + x("du -sh /data/registry 2>/dev/null"))

    sh(["docker", "rm", "-f", D])
    sh(["docker", "volume", "rm", "-f", "harbor-dind-data"])
    cab = ["# SALIDA — Harbor (vídeo 331)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Harbor {VER} con Trivy, dentro de docker:dind."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
