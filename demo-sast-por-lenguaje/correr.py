# -*- coding: utf-8 -*-
"""Demo de «Un escáner de seguridad para cada lenguaje en tu pipeline» (cultura-devops).

La MISMA aplicación vulnerable a propósito (app/, ver LEEME.md) en PHP, Python, Go, Java y Node. Para cada lenguaje, su
analizador de código (SAST) y su analizador de dependencias (SCA), cada uno en su contenedor con la versión fijada:
  PHP    · Psalm 6.20.1 --taint-analysis       · composer audit (Composer 2.10.3)
  Python · Bandit 1.9.4                         · pip-audit 2.10.1
  Go     · gosec v2.30.0                        · govulncheck v1.9.0
  Java   · SpotBugs 4.9.3 + Find Security Bugs 1.14.0 · Trivy 0.75.0 (en vez de OWASP Dependency-Check: ver nota en SALIDA.md)
  Node   · njsscan 1.0.1                        · npm audit (npm 10.9.9)
Se mide SOLO el análisis (la instalación de cada herramienta va aparte), y cada hallazgo se puntúa con puntuar.py.
Al final, el mismo control como workflow de GitHub Actions (app/.github/workflows/seguridad.yml), ejecutado en local con act.
Todo lo que arranca lleva la etiqueta demo=sast y se borra al terminar.

    python correr.py   -> SALIDA.md + salida/*.json
"""
import json
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import puntuar as P

AQUI = Path(__file__).parent
SAL = AQUI / "salida"
OUT = []
ACT = "v0.2.89"


def run(args, timeout=1800):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def win(p):
    return str(p).replace("\\", "/")


def arrancar(nombre, imagen, *extra):
    run(["docker", "rm", "-f", nombre])
    s, rc = run(["docker", "run", "-d", "--name", nombre, "--label", "demo=sast", "-v", f"{win(AQUI / 'app')}:/src:ro",
                 "-v", f"{win(SAL)}:/out", *extra, "--entrypoint", "sh", imagen, "-c", "cp -r /src /w && sleep infinity"])
    assert rc == 0, s
    time.sleep(1)


def ex(nombre, cmd, timeout=1800):
    return run(["docker", "exec", "-w", "/w", nombre, "sh", "-c", cmd], timeout)


def medir(nombre, cmd):
    t0 = time.perf_counter()
    s, rc = ex(nombre, cmd)
    return s, rc, time.perf_counter() - t0


def bloque(titulo, mostrado, salida, rc, seg=None, nota=None):
    pie = f"(código de salida {rc}" + (f" · {seg:.1f} s de análisis)" if seg is not None else ")")
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{salida}\n```\n{pie}\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}" + (f" {seg:.1f}s" if seg is not None else ""))


def recorta(texto, n=40):
    lineas = texto.splitlines()
    return "\n".join(lineas[:n] + ([f"… ({len(lineas) - n} líneas más)"] if len(lineas) > n else []))


TABLA = []  # (lenguaje, herramienta, puntuación, segundos)


def anota(lang, herramienta, hallazgos, seg):
    r = P.puntuar(hallazgos, [lang])[lang]
    TABLA.append((lang, herramienta, r, seg))
    OUT.append(f"**Puntuación** ({herramienta}, {lang}): {P.fila(r)}\n")


def php():
    OUT.append("## PHP · Psalm (taint analysis) + composer audit\n")
    n = "sast-php"
    arrancar(n, "composer:2.10.3")
    ex(n, "mkdir -p /t && cd /t && composer require -q --no-interaction vimeo/psalm:6.20.1 && cd /w/php && composer dump-autoload -q && "
          "/t/vendor/bin/psalm --init . 1 >/dev/null")
    bloque("versión", "psalm --version", *ex(n, "/t/vendor/bin/psalm --version")[:2])
    s, rc, seg = medir(n, "cd php && /t/vendor/bin/psalm --taint-analysis --no-cache --no-progress --output-format=json "
                          "> /out/psalm.json; echo $?")
    rc = int(s.strip().splitlines()[-1])
    hall =[(f"php/{i['file_name']}", i["line_from"], i["type"], i["message"]) for i in json.loads((SAL / "psalm.json").read_text())]
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[2]}  {h[3]}" for h in hall) or "(sin hallazgos)"
    bloque("Psalm --taint-analysis", "psalm --taint-analysis", vista, rc, seg)
    anota("php", "Psalm", hall, seg)
    # sonda: ¿por qué no vio las dos inyecciones SQL?
    ex(n, "mkdir -p /sonda && cd /sonda && echo '{\"name\":\"demo/sonda\"}' > composer.json && composer dump-autoload -q && "
          "printf '<?php\\n$db = new PDO(\"sqlite:x\");\\n$db->query(\"SELECT \" . $_GET[\"a\"]);\\n"
          "$m = new mysqli();\\n$m->query(\"SELECT \" . $_GET[\"b\"]);\\nmysqli_query($m, \"SELECT \" . $_GET[\"c\"]);\\n' > sonda.php && "
          "/t/vendor/bin/psalm --init . 1 >/dev/null")
    bloque("la sonda", "cat sonda.php", *ex(n, "cat /sonda/sonda.php")[:2])
    s, rc = ex(n, "cd /sonda && /t/vendor/bin/psalm --taint-analysis --no-cache --no-progress --monochrome --output-format=compact "
                  "| grep -E 'Tainted|errors|No errors'")
    bloque("Psalm sobre la sonda: PDO contra mysqli", "psalm --taint-analysis sonda.php", s, rc,
           nota="Misma consulta, mismo dato del usuario: con mysqli (líneas 5 y 6) sale TaintedSql; con PDO (línea 3), nada.")
    # dependencias
    s, rc = ex(n, "cd php && composer update --no-install --no-interaction > /tmp/cu.log 2>&1; r=$?; "
                  "grep -E 'Problem|requires|security advisories' /tmp/cu.log | "
                  "sed -E 's/\\(\"PKSA[^)]*\\)/(…14 avisos…)/' | cut -c1-260; exit $r")
    bloque("Composer se niega a instalar la versión vieja", "composer update", s, rc,
           nota="Composer 2.10.3 bloquea por defecto instalar una versión con avisos de seguridad publicados (policy.advisories.block).")
    t = medir(n, "cd php && composer config policy.advisories.block false && composer update --no-install --no-interaction -q && "
                 "composer audit --locked --format=json > /out/composer-audit.json; echo")
    d = json.loads((SAL / "composer-audit.json").read_text())
    avisos = [a for v in d["advisories"].values() for a in v]
    sev = {}
    for a in avisos:
        sev[a.get("severity") or "?"] = sev.get(a.get("severity") or "?", 0) + 1
    vista = f"{len(avisos)} avisos en guzzlehttp/guzzle 7.4.0 · por gravedad: {sev}\n" + "\n".join(
        f"  {a['cve'] or a['advisoryId']}  {a.get('severity')}  {a['title'][:70]}" for a in avisos[:5]) + "\n  …"
    bloque("composer audit (con el bloqueo desactivado, solo en esta copia)", "composer audit --locked", vista, 0, t[2])


def python():
    OUT.append("## Python · Bandit + pip-audit\n")
    n = "sast-python"
    arrancar(n, "python:3.13-slim")
    ex(n, "pip install -q --root-user-action=ignore bandit==1.9.4 pip-audit==2.10.1")
    bloque("versiones", "bandit --version; pip-audit --version", *ex(n, "bandit --version | head -1; pip-audit --version")[:2])
    s, rc, seg = medir(n, "bandit -r python -f json -o /out/bandit.json -q; echo $?")
    d = json.loads((SAL / "bandit.json").read_text())
    hall = [(r["filename"], r["line_number"], r["test_id"], r["issue_text"]) for r in d["results"]]
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[2]}  {h[3]}" for h in hall)
    bloque("Bandit", "bandit -r python", vista, int(s.strip() or 0), seg)
    anota("python", "Bandit", hall, seg)
    s, rc, seg = medir(n, "pip-audit -r python/requirements.txt -f json -o /out/pip-audit.json >/dev/null 2>&1; echo $?")
    d = json.loads((SAL / "pip-audit.json").read_text())
    deps = [(x["name"], x["version"], len(x["vulns"])) for x in d["dependencies"] if x.get("vulns")]
    vista = "\n".join(f"{a} {b}: {c} vulnerabilidades" for a, b, c in deps) + f"\nTOTAL: {sum(c for *_, c in deps)}"
    bloque("pip-audit", "pip-audit -r requirements.txt", vista, int(s.strip() or 0), seg,
           "requests 2.25.1 trae dependencias viejas (idna, urllib3): pip-audit las revisa también.")


def go():
    OUT.append("## Go · gosec + govulncheck\n")
    n = "sast-go"
    arrancar(n, "golang:1.27.2")
    ex(n, "cd go && go mod tidy && go install github.com/securego/gosec/v2/cmd/gosec@v2.30.0 && "
          "go install golang.org/x/vuln/cmd/govulncheck@v1.9.0")
    bloque("versiones", "go version; govulncheck -version", *ex(n, "go version; govulncheck -version | head -3")[:2])
    s, rc, seg = medir(n, "cd go && gosec -quiet -fmt json -out /out/gosec.json ./... ; echo $?")
    d = json.loads((SAL / "gosec.json").read_text())
    hall = [(f"go/{Path(i['file']).name}", i["line"], i["rule_id"], i["details"]) for i in d["Issues"]]
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[2]}  {h[3]}" for h in sorted(hall, key=lambda h: (h[0], int(h[1]))))
    bloque("gosec", "gosec ./...", vista, int(s.strip() or 0), seg)
    anota("go", "gosec", hall, seg)
    s, rc = ex(n, "rm -rf /sin-sum && cp -r go /sin-sum && cd /sin-sum && rm go.sum && "
                  "gosec -quiet ./... 2>&1 | grep -E 'Golang errors|missing go.sum|Issues :|G70[0-9]' | head -8")
    bloque("gosec en una copia SIN go.sum", "rm go.sum && gosec ./...", s, rc,
           nota="Sin go.sum, gosec no puede cargar los tipos: avisa de «Golang errors» y se salta el análisis de taint "
                "(G701/G702): 7 hallazgos en vez de 16. El trabajo de act sigue en rojo, pero con menos de la mitad.")
    s, rc, seg = medir(n, "cd go && govulncheck ./... 2>&1")
    bloque("govulncheck", "govulncheck ./...", recorta(s, 25), rc, seg,
           "govulncheck no solo dice «tienes una versión vieja»: dice si tu código LLAMA a la función vulnerable.")


def java():
    OUT.append("## Java · SpotBugs + Find Security Bugs, y Trivy para las dependencias\n")
    n = "sast-java"
    arrancar(n, "maven:3.9.16-eclipse-temurin-21", "-v", "fabrica-m2:/root/.m2")
    ex(n, "cd java && mvn -q -B compile")
    bloque("versión", "mvn -v", *ex(n, "mvn -v | head -1")[:2])
    s, rc, seg = medir(n, "cd java && mvn -q -B com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0:spotbugs >/dev/null 2>&1; "
                          "cp target/spotbugsXml.xml /out/spotbugs.xml; echo")
    raiz = ET.parse(SAL / "spotbugs.xml").getroot()
    hall = []
    for b in raiz.iter("BugInstance"):
        sl = [x for x in b.findall("SourceLine") if x.get("primary") == "true"] or list(b.iter("SourceLine"))
        hall.append((f"java/{sl[0].get('sourcefile')}", sl[0].get("start"), b.get("type"), b.get("category")))
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[3]}  {h[2]}" for h in sorted(hall, key=lambda h: (h[0], int(h[1]))))
    bloque("SpotBugs + Find Security Bugs", "mvn spotbugs:spotbugs", vista, 0, seg)
    anota("java", "SpotBugs+FSB", hall, seg)
    t = "sast-trivy"
    arrancar(t, "aquasec/trivy:0.75.0", "-v", "fabrica-trivy:/root/.cache")
    ex(t, "trivy image --download-db-only --quiet")  # baja la base de datos fuera de la medida
    s, rc, seg = medir(t, "trivy fs --scanners vuln --quiet --offline-scan --skip-db-update --format table /w/java 2>&1 | "
                          "grep -E 'Total|CVE-2021-44228|CVE-2021-45046|log4j-core' | head -6")
    bloque("Trivy sobre el pom.xml", "trivy fs --scanners vuln --offline-scan java", s, rc, seg,
           "OWASP Dependency-Check es la opción clásica para Java, pero la primera vez descarga la base completa de la NVD (sin "
           "clave de API, horas). Trivy hace el mismo trabajo sobre el pom.xml en segundos; es lo que se usa aquí. --offline-scan: "
           "sin preguntar a Maven Central, que el día de la demo respondió 429 (demasiadas peticiones); así ve las dependencias "
           "directas del pom, no las transitivas (log4j-api).")


def node():
    OUT.append("## Node · njsscan + npm audit\n")
    n = "sast-node"
    arrancar(n, "python:3.13-slim")
    ex(n, "pip install -q --root-user-action=ignore njsscan==1.0.1")
    s, rc, seg = medir(n, "njsscan --json -o /out/njsscan.json node >/dev/null 2>&1; echo $?")
    d = json.loads((SAL / "njsscan.json").read_text())
    hall = []
    for grupo in ("nodejs", "templates"):
        for regla, v in d.get(grupo, {}).items():
            for f in v.get("files", []):
                hall.append((f["file_path"], f["match_lines"][0], regla, v["metadata"].get("description", "")))
    vista = "\n".join(f"{h[0]}:{h[1]}  {h[2]}" for h in hall) or "(sin hallazgos)"
    bloque("njsscan", "njsscan node", vista, int(s.strip() or 0), seg)
    anota("node", "njsscan", hall, seg)
    m = "sast-npm"
    arrancar(m, "node:22-bookworm-slim")
    ex(m, "cd node && npm install --package-lock-only --ignore-scripts --no-audit -q")
    s, rc, seg = medir(m, "cd node && npm audit --json > /out/npm-audit.json; echo $?")
    d = json.loads((SAL / "npm-audit.json").read_text())
    vista = (f"vulnerabilidades por gravedad: {d['metadata']['vulnerabilities']}\npaquetes afectados: " +
             ", ".join(sorted(d["vulnerabilities"])))
    bloque("npm audit", "npm audit", vista, int(s.strip() or 0), seg)


def con_act():
    OUT.append("## Todo junto: el workflow de GitHub Actions, ejecutado en local con act\n")
    n = "sast-act"
    run(["docker", "rm", "-f", n])
    run(["docker", "run", "-d", "--name", n, "--label", "demo=sast", "-v", "//var/run/docker.sock:/var/run/docker.sock",
         "-v", f"{win(AQUI / 'app')}:/src:ro", "alpine:3.22", "sh", "-c", "cp -r /src /w && sleep infinity"])
    ex(n, "apk add -q curl git docker-cli >/dev/null && "
          f"curl -sL https://github.com/nektos/act/releases/download/{ACT}/act_Linux_x86_64.tar.gz | tar xz -C /usr/local/bin act && "
          "git init -q && git config user.email a@b.c && git config user.name lab && git add -A && git commit -qm inicio")
    bloque("el workflow", "cat .github/workflows/seguridad.yml", *ex(n, "cat .github/workflows/seguridad.yml")[:2])
    bloque("los trabajos", "act -l", *ex(n, "act -l")[:2])
    t0 = time.perf_counter()
    ex(n, "act push --rm -P ubuntu-latest=node:22-bookworm-slim > /tmp/act.log 2>&1", timeout=3600)
    seg = time.perf_counter() - t0
    ex(n, "cp /tmp/act.log /tmp/act-completo.log")
    run(["docker", "cp", f"{n}:/tmp/act.log", str(SAL / "act.log")])
    s, rc = ex(n, "grep -E '(Success - Main|Failure - Main)' /tmp/act.log | grep -v checkout | sed 's/ \\[[0-9.]*m\\?s\\]//' | sort")
    bloque("act push", "act push", s, rc, seg,
           "Cada trabajo es independiente: todos corren, y el pipeline queda en rojo si alguno encuentra algo.")
    # por qué falló cada uno, sacado del registro completo de act
    import re
    reg = re.sub(r"\x1b\[[0-9;]*m", "", (SAL / "act.log").read_text(encoding="utf-8", errors="replace"))
    por = {}
    for linea in reg.splitlines():
        m = re.match(r"\[seguridad/([a-z-]+)\s*\]\s+\|\s?(.*)", linea)
        if m:
            por.setdefault(m.group(1), []).append(m.group(2))
    motivos = {
        "php": lambda L: next((x.strip() for x in L if re.search(r"\d+ errors? found", x)), "?") + " (Psalm)",
        "python": lambda L: f"{sum('>> Issue:' in x for x in L)} hallazgos (Bandit)",
        "go": lambda L: next((x.strip() for x in L if "Issues :" in x), "?") + " (gosec)",
        "java": lambda L: str(sum(bool(re.match(r"\[ERROR\] (High|Medium|Low):", x)) for x in L)) + " hallazgos (spotbugs:check)",
        "java-dependencias": lambda L: next((x.strip() for x in L if x.startswith("Total:")), "?") + " (Trivy)",
        "node": lambda L: next((x.strip() for x in L if re.search(r"\d+ vulnerabilities \(", x)), "?") + " (npm audit)",
        "node-codigo": lambda L: f"{sum('RULE ID' in x for x in L)} regla(s) disparada(s) (njsscan)",
    }
    s = "\n".join(f"{job:18} {f(por.get(job, []))}" for job, f in motivos.items())
    bloque("por qué falló cada trabajo (contado en el registro de act)", "grep … act.log", s, 0)


def main():
    SAL.mkdir(exist_ok=True)
    OUT.append(f"# SALIDA — Un escáner de seguridad para cada lenguaje (cultura-devops)\n\nGenerado "
               f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. Código vulnerable A PROPÓSITO (app/, "
               f"ver LEEME.md): nunca se despliega.\n\nVerdad de referencia en cada lenguaje: V1 inyección SQL · V2 inyección de "
               f"comandos · V3 inyección SQL armada en otro archivo · S1 consulta con parámetros (segura) · S2 id convertido a "
               f"entero (seguro). ✔/✘ = detectó o no V1, V2, V3.\n")
    try:
        for f in (php, python, go, java, node):
            f()
        OUT.append("## Resumen\n\n| Lenguaje | Herramienta | V1 V2 V3 | Falsos positivos | Otros avisos | Segundos |\n|---|---|---|---|---|---|")
        for lang, h, r, seg in TABLA:
            OUT.append(f"| {lang} | {h} | {''.join('✔' if r[c] else '✘' for c in ('V1', 'V2', 'V3'))} | "
                       f"{','.join(sorted(r['fp'])) or '—'} | {r['otros']} | {seg:.1f} |")
        OUT.append("")
        con_act()
    finally:
        (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
        ids, _ = run(["docker", "ps", "-aq", "--filter", "label=demo=sast"])
        if ids:
            run(["docker", "rm", "-f", *ids.split()])
        ids, _ = run(["docker", "ps", "-aq", "--filter", "name=act-seguridad-"])
        if ids:
            run(["docker", "rm", "-f", *ids.split()])
        print("ok SALIDA.md")


if __name__ == "__main__":
    main()
