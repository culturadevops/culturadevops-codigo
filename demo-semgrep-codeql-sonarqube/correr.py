# -*- coding: utf-8 -*-
"""Demo de «Semgrep vs CodeQL vs SonarQube» (cultura-devops).

La MISMA aplicación vulnerable a propósito que el vídeo de «un escáner por lenguaje» (../demo-sast-por-lenguaje/app, ver su
LEEME.md), en PHP, Python, Go, Java y Node, pasada por los tres analizadores «para todos los lenguajes», versiones fijadas:
  · Semgrep CE 1.181.1 con el conjunto de reglas p/default (sin cuenta, --metrics=off);
  · CodeQL CLI 2.27.3 (bundle oficial) con las consultas por defecto de cada lenguaje; no tiene PHP;
  · SonarQube Community Build 26.10.0.133078 en Docker + sonar-scanner-cli 12.2.0.4256 (scanner 8.1.0).
Cada hallazgo se puntúa con ../demo-sast-por-lenguaje/puntuar.py: aciertos (V1, V2, V3), falsos positivos (S1, S2) y otros avisos.
Todo lo que arranca lleva la etiqueta demo=sast y se borra al terminar.

    python correr.py   -> SALIDA.md + salida/*
"""
import json
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
BASE = AQUI.parent / "demo-sast-por-lenguaje"
sys.path.insert(0, str(BASE))
import puntuar as P  # noqa: E402

SAL = AQUI / "salida"
OUT = []
SEMGREP = "semgrep/semgrep:1.181.1"
CODEQL = "2.27.3"
SONAR = "sonarqube:26.10.0.133078-community"
SCANNER = "sonarsource/sonar-scanner-cli:12.2.0.4256_8.1.0"
RES = {}  # herramienta -> {"hall": [...], "seg": float, "langs": [...]}


def run(args, timeout=3600):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def win(p):
    return str(p).replace("\\", "/")


def bloque(titulo, mostrado, salida, rc, seg=None, nota=None):
    pie = f"(código de salida {rc}" + (f" · {seg:.1f} s)" if seg is not None else ")")
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{salida}\n```\n{pie}\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}" + (f" {seg:.1f}s" if seg is not None else ""))


def lista(hall):
    return "\n".join(f"{h[0]}:{h[1]}  {h[2]}" for h in sorted(hall, key=lambda h: (str(h[0]), int(h[1] or 0))))


def semgrep():
    OUT.append("## Semgrep CE\n")
    run(["docker", "pull", "-q", SEMGREP])
    t0 = time.perf_counter()
    s, rc = run(["docker", "run", "--rm", "--label", "demo=sast", "-v", f"{win(BASE / 'app')}:/src:ro", "-v", f"{win(SAL)}:/out",
                 "-w", "/src", SEMGREP, "semgrep", "scan", "--metrics=off", "--config", "p/default", "--json",
                 "-o", "/out/semgrep.json", "--quiet", "."])
    seg = time.perf_counter() - t0
    d = json.loads((SAL / "semgrep.json").read_text(encoding="utf-8"))
    hall = [(r["path"], r["start"]["line"], r["check_id"].split(".")[-1], r["extra"].get("message", "")) for r in d["results"]]
    ver, _ = run(["docker", "run", "--rm", SEMGREP, "semgrep", "--version"])
    bloque(f"Semgrep {next(l for l in ver.splitlines() if l[:1].isdigit())} · p/default", "semgrep scan --config p/default .", lista(hall), rc, seg,
           "El tiempo incluye bajar las reglas del registro de Semgrep (no hace falta cuenta).")
    RES["Semgrep"] = {"hall": hall, "seg": seg, "langs": P.LENGUAJES}


def codeql():
    OUT.append("## CodeQL\n")
    n = "sast-codeql"
    run(["docker", "rm", "-f", n])
    run(["docker", "run", "-d", "--name", n, "--label", "demo=sast", "-v", "fabrica-codeql:/opt", "-v", f"{win(BASE / 'app')}:/src:ro",
         "-v", f"{win(SAL)}:/out", "golang:1.27.2", "sh", "-c", "cp -r /src /w && mkdir -p /db && sleep infinity"])
    s, rc = run(["docker", "exec", n, "sh", "-c",
                 "cd /opt && if [ ! -x codeql/codeql ]; then curl -sSL -o b.tgz https://github.com/github/codeql-action/releases/download/"
                 f"codeql-bundle-v{CODEQL}/codeql-bundle-linux64.tar.gz && tar xzf b.tgz && rm b.tgz; fi; "
                 "codeql/codeql version | head -1; codeql/codeql resolve languages | cut -d' ' -f1 | sort | tr '\\n' ' '"])
    bloque("versión y lenguajes que entiende", "codeql version; codeql resolve languages", s, rc,
           nota="No hay «php» en la lista: CodeQL no analiza PHP.")
    hall, total = [], 0.0
    for lang, carpeta, modo in (("python", "python", ""), ("javascript", "node", ""), ("go", "go", "--build-mode=autobuild"),
                                ("java", "java", "--build-mode=none")):
        t0 = time.perf_counter()
        s, rc = run(["docker", "exec", n, "sh", "-c",
                     f"export PATH=/opt/codeql:$PATH; codeql database create /db/{lang} --language={lang} --source-root=/w/{carpeta} "
                     f"{modo} --overwrite -q && codeql database analyze /db/{lang} codeql/{lang}-queries --format=sarif-latest "
                     f"--output=/out/codeql-{lang}.sarif -q"])
        seg = time.perf_counter() - t0
        total += seg
        d = json.loads((SAL / f"codeql-{lang}.sarif").read_text(encoding="utf-8"))
        h = []
        for r in d["runs"][0]["results"]:
            loc = r["locations"][0]["physicalLocation"]
            h.append((f"{carpeta}/{loc['artifactLocation']['uri']}", loc["region"]["startLine"], r["ruleId"], r["message"]["text"]))
        hall += h
        bloque(f"CodeQL · {lang}", f"codeql database create … && codeql database analyze … codeql/{lang}-queries",
               lista(h) or "(sin hallazgos)", rc, seg)
    RES["CodeQL"] = {"hall": hall, "seg": total, "langs": ["python", "node", "go", "java"]}


def _api(ruta, auth, datos=None):
    req = urllib.request.Request(f"http://127.0.0.1:9000{ruta}", data=urllib.parse.urlencode(datos).encode() if datos else None,
                                 headers={"Authorization": "Basic " + b64encode(auth.encode()).decode()})
    with urllib.request.urlopen(req, timeout=60) as r:
        cuerpo = r.read()
        return json.loads(cuerpo) if cuerpo else {}


def sonarqube():
    OUT.append("## SonarQube Community Build\n")
    n = "sast-sonarqube"
    run(["docker", "rm", "-f", n])
    run(["docker", "run", "-d", "--name", n, "--label", "demo=sast", "-p", "127.0.0.1:9000:9000",
         "-e", "SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true", "-e", "SONAR_SEARCH_JAVAADDITIONALOPTS=-Dnode.store.allow_mmap=false", SONAR])
    t0 = time.perf_counter()
    estado = ""
    while time.perf_counter() - t0 < 600:
        try:
            estado = json.loads(urllib.request.urlopen("http://127.0.0.1:9000/api/system/status", timeout=5).read())["status"]
        except Exception:  # noqa: BLE001 (todavía arrancando)
            estado = "arrancando"
        if estado == "UP":
            break
        time.sleep(5)
    arranque = time.perf_counter() - t0
    clave = "Demo-" + secrets.token_hex(8) + "!"   # contraseña de un servidor local que se borra al terminar
    _api("/api/users/change_password", "admin:admin", {"login": "admin", "previousPassword": "admin", "password": clave})
    token = _api("/api/user_tokens/generate", f"admin:{clave}", {"name": "demo", "type": "GLOBAL_ANALYSIS_TOKEN"})["token"]
    version = urllib.request.urlopen("http://127.0.0.1:9000/api/server/version", timeout=10).read().decode()
    bloque("el servidor", "docker run sonarqube:community", f"SonarQube {version} · {estado} en {arranque:.0f} s", 0,
           nota="SonarQube necesita un servidor (con su base de datos y su Elasticsearch) antes de analizar nada.")
    # Java se analiza con los .class: se compila antes, en una copia
    copia = SAL / "copia"
    run(["docker", "run", "--rm", "--label", "demo=sast", "-v", f"{win(BASE / 'app')}:/src:ro", "-v", f"{win(SAL)}:/out",
         "-v", "fabrica-m2:/root/.m2", "maven:3.9.16-eclipse-temurin-21", "sh", "-c",
         "rm -rf /out/copia && cp -r /src /out/copia && cd /out/copia/java && mvn -q -B compile"])
    t0 = time.perf_counter()
    s, rc = run(["docker", "run", "--rm", "--label", "demo=sast", "--network", f"container:{n}", "-v", f"{win(copia)}:/usr/src",
                 "-e", "SONAR_HOST_URL=http://localhost:9000", "-e", f"SONAR_TOKEN={token}", SCANNER,
                 "-Dsonar.projectKey=tienda-vulnerable", "-Dsonar.sources=.", "-Dsonar.java.binaries=java/target/classes",
                 "-Dsonar.qualitygate.wait=true"])
    seg = time.perf_counter() - t0
    fin = "\n".join(l for l in s.splitlines() if "ANALYSIS SUCCESSFUL" in l or "QUALITY GATE" in l or "EXECUTION" in l)
    bloque("sonar-scanner", "sonar-scanner -Dsonar.projectKey=tienda-vulnerable …", fin, rc, seg)
    seguridad = _api("/api/issues/search?componentKeys=tienda-vulnerable&ps=500&impactSoftwareQualities=SECURITY", f"admin:{clave}")
    puntos = _api("/api/hotspots/search?project=tienda-vulnerable&ps=500", f"admin:{clave}")
    todos = _api("/api/issues/search?componentKeys=tienda-vulnerable&ps=1", f"admin:{clave}")
    hall = [(i["component"].split(":", 1)[-1], i.get("line", 0), i["rule"], i["message"]) for i in seguridad["issues"]]
    hall += [(h["component"].split(":", 1)[-1], h.get("line", 0), h["ruleKey"], h["message"]) for h in puntos.get("hotspots", [])]
    (SAL / "sonarqube.json").write_text(json.dumps({"seguridad": seguridad, "hotspots": puntos}, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[2]}  {h[3][:80]}" for h in sorted(hall, key=lambda h: (h[0], int(h[1]))))
    bloque("lo que marca como seguridad", "GET /api/issues/search?impactSoftwareQualities=SECURITY (+ /api/hotspots/search)",
           vista + f"\n\n(issues de todo tipo en el proyecto: {todos['total']})", 0,
           nota="En la Community Build no hay análisis de taint: lo de seguridad son reglas que piden revisar la línea.")
    RES["SonarQube CB"] = {"hall": hall, "seg": seg, "langs": P.LENGUAJES}


def main():
    SAL.mkdir(exist_ok=True)
    OUT.append(f"# SALIDA — Semgrep vs CodeQL vs SonarQube (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
               f"con `python correr.py`. Código vulnerable A PROPÓSITO (../demo-sast-por-lenguaje/app): nunca se despliega.\n\n"
               f"En cada lenguaje: V1 inyección SQL · V2 inyección de comandos · V3 inyección SQL armada en otro archivo (aciertos) · "
               f"S1 consulta con parámetros · S2 id convertido a entero (seguros: si se marcan, son falsos positivos).\n")
    try:
        semgrep()
        codeql()
        sonarqube()
        OUT.append("## Resumen por lenguaje\n\n| Herramienta | Lenguaje | V1 V2 V3 | Falsos positivos | Otros avisos |\n|---|---|---|---|---|")
        tot = []
        for h, r in RES.items():
            p = P.puntuar(r["hall"])
            ac = fp = ot = 0
            for lang in P.LENGUAJES:
                x = p[lang]
                if lang not in r["langs"]:
                    OUT.append(f"| {h} | {lang} | no lo soporta | — | — |")
                    continue
                OUT.append(f"| {h} | {lang} | {''.join('✔' if x[c] else '✘' for c in ('V1', 'V2', 'V3'))} | "
                           f"{','.join(sorted(x['fp'])) or '—'} | {x['otros']} |")
                ac += sum(x[c] for c in ("V1", "V2", "V3"))
                fp += len(x["fp"])
                ot += x["otros"]
            tot.append((h, ac, 3 * len(r["langs"]), fp, ot, r["seg"]))
        OUT.append("\n## Resumen total\n\n| Herramienta | Aciertos | Falsos positivos | Otros avisos | Segundos |\n|---|---|---|---|---|")
        for h, ac, de, fp, ot, seg in tot:
            OUT.append(f"| {h} | {ac}/{de} | {fp} | {ot} | {seg:.0f} |")
        OUT.append("")
    finally:
        (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
        ids, _ = run(["docker", "ps", "-aq", "--filter", "label=demo=sast"])
        if ids:
            run(["docker", "rm", "-f", *ids.split()])
        print("ok SALIDA.md")


if __name__ == "__main__":
    main()
