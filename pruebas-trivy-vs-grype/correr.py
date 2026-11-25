# -*- coding: utf-8 -*-
"""Trivy vs Grype — banco de pruebas del vídeo 338 (cultura-devops, serie versus).

La MISMA imagen escaneada con los dos, y la MISMA pregunta: cuántas vulnerabilidades, en qué se
diferencian, y por qué no coinciden. Trivy 0.75 y Grype 0.120, los dos en Docker, leyendo la
imagen desde el socket de Docker del anfitrión. Sin red tras la primera descarga de bases.

    python correr.py
"""
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TRIVY = "aquasec/trivy:latest"
GRYPE = "anchore/grype:latest"
IMAGEN = "python:3.9-slim"   # una imagen vieja y popular, con de todo
salida = []


def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.stdout, (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1200]}\n", flush=True)


SOCK = ["-v", "//var/run/docker.sock:/var/run/docker.sock"]


def trivy_json(img):
    out, _ = sh(["docker", "run", "--rm", *SOCK, "-v", "trivy-cache:/root/.cache", TRIVY,
                 "image", "--quiet", "--format", "json", "--scanners", "vuln", img], timeout=1800)
    return json.loads(out)


def grype_json(img):
    out, _ = sh(["docker", "run", "--rm", *SOCK, "-v", "grype-db:/.cache/grype", "-e", "GRYPE_DB_CACHE_DIR=/.cache/grype",
                 GRYPE, "-q", "-o", "json", "docker:" + img], timeout=1800)
    return json.loads(out)


def sev_trivy(d):
    c, ids = Counter(), {}
    for res in d.get("Results", []):
        for v in res.get("Vulnerabilities", []) or []:
            c[v.get("Severity", "UNKNOWN").title()] += 1
            ids.setdefault(v["VulnerabilityID"], v.get("PkgName"))
    return c, ids


def sev_grype(d):
    c, ids = Counter(), {}
    for m in d.get("matches", []):
        c[m["vulnerability"]["severity"].title()] += 1
        ids.setdefault(m["vulnerability"]["id"], m["artifact"]["name"])
    return c, ids


def tabla(ct, cg):
    orden = ["Critical", "High", "Medium", "Low", "Negligible", "Unknown"]
    filas = [f"{'severidad':<12} {'Trivy':>8} {'Grype':>8}"]
    for s in orden:
        if ct.get(s) or cg.get(s):
            filas.append(f"{s:<12} {ct.get(s, 0):>8} {cg.get(s, 0):>8}")
    filas.append(f"{'TOTAL':<12} {sum(ct.values()):>8} {sum(cg.values()):>8}")
    return "\n".join(filas)


def main():
    sh(["docker", "pull", "-q", IMAGEN], timeout=600)
    salida.append(f"\n## 1 · La misma imagen: {IMAGEN}")
    anota("versiones", "trivy --version; grype version",
          sh(["docker", "run", "--rm", TRIVY, "--version"])[1].split("\n")[0] + "\n"
          + "grype " + [l for l in sh(["docker", "run", "--rm", GRYPE, "version"])[1].splitlines() if "Version:" in l][0].split()[-1])

    salida.append("\n## 2 · Escanear con cada uno")
    import time
    t = time.time()
    dt = trivy_json(IMAGEN)
    tt = time.time() - t
    t = time.time()
    dg = grype_json(IMAGEN)
    tg = time.time() - t
    ct, idt = sev_trivy(dt)
    cg, idg = sev_grype(dg)
    anota("tiempos (con las bases ya descargadas)", "time docker run … trivy / grype",
          f"Trivy: {tt:.0f} s\nGrype: {tg:.0f} s")
    anota("vulnerabilidades por severidad", "recuento de cada salida JSON", tabla(ct, cg))

    salida.append("\n## 3 · Por qué no coinciden")
    solo_t = set(idt) - set(idg)
    solo_g = set(idg) - set(idt)
    comun = set(idt) & set(idg)
    anota("solapamiento de CVE", "intersección de identificadores",
          f"en los dos:   {len(comun)}\nsolo en Trivy: {len(solo_t)}\nsolo en Grype: {len(solo_g)}")
    anota("ejemplos que solo ve Trivy", "CVE y paquete",
          "\n".join(f"{c}  {idt[c]}" for c in list(solo_t)[:6]) or "(ninguno)")
    anota("ejemplos que solo ve Grype", "CVE y paquete",
          "\n".join(f"{c}  {idg[c]}" for c in list(solo_g)[:6]) or "(ninguno)")
    # fuentes de datos de cada uno
    fuentes_t = Counter(v.get("DataSource", {}).get("Name", "?")
                        for res in dt.get("Results", []) for v in (res.get("Vulnerabilities") or []))
    anota("fuentes de datos de Trivy", "campo DataSource de cada hallazgo",
          "\n".join(f"{n}: {c}" for n, c in fuentes_t.most_common()))
    fuentes_g = Counter(m["vulnerability"].get("namespace", "?") for m in dg.get("matches", []))
    anota("fuentes de datos de Grype", "campo namespace de cada hallazgo",
          "\n".join(f"{n}: {c}" for n, c in fuentes_g.most_common(8)))

    salida.append("\n## 4 · Solo las que tienen arreglo")
    fix_t = sum(1 for res in dt.get("Results", []) for v in (res.get("Vulnerabilities") or []) if v.get("FixedVersion"))
    fix_g = sum(1 for m in dg.get("matches", []) if any(f for f in m["vulnerability"].get("fix", {}).get("versions", [])))
    anota("¿cuántas se arreglan actualizando?", "FixedVersion / fix.versions",
          f"Trivy: {fix_t} de {sum(ct.values())} con arreglo\nGrype: {fix_g} de {sum(cg.values())} con arreglo")

    salida.append("\n## 5 · Fallar la construcción si hay algo crítico")
    _, st = sh(["docker", "run", "--rm", *SOCK, "-v", "trivy-cache:/root/.cache", TRIVY, "image",
                "--quiet", "--scanners", "vuln", "--severity", "CRITICAL", "--exit-code", "1", IMAGEN], timeout=900)
    anota("Trivy en el pipeline", "trivy image --severity CRITICAL --exit-code 1",
          "\n".join(st.splitlines()[-6:]) + f"\ncódigo de salida: {1 if 'CRITICAL' in st else '?'}")
    _, sg = sh(["docker", "run", "--rm", *SOCK, "-v", "grype-db:/.cache/grype", "-e", "GRYPE_DB_CACHE_DIR=/.cache/grype",
                GRYPE, "--fail-on", "critical", "-q", "docker:" + IMAGEN], timeout=900)
    anota("Grype en el pipeline", "grype --fail-on critical",
          "\n".join(sg.splitlines()[-4:]))

    salida.append("\n## 6 · Una imagen limpia")
    sh(["docker", "pull", "-q", "alpine:3.22"], timeout=300)
    dt2 = trivy_json("alpine:3.22")
    dg2 = grype_json("alpine:3.22")
    ct2, _ = sev_trivy(dt2)
    cg2, _ = sev_grype(dg2)
    anota("alpine:3.22", "escaneo con los dos", tabla(ct2, cg2))

    cab = ["# SALIDA — Trivy vs Grype (vídeo 338)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Trivy ({TRIVY}) y Grype ({GRYPE}) sobre {IMAGEN} y alpine:3.22."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
