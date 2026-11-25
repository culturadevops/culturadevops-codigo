# -*- coding: utf-8 -*-
"""Banco del 878 · el pipeline de Spring PetClinic, base y cada mejora por separado.

Requiere: preparar_repo.sh, la imagen jk-b-agente-petclinic:1 (Dockerfile.agente) y levantar_878.sh (jk-b-jenkins-878, 28078).
Seis variantes (jenkinsfiles/*.Jenkinsfile), 4 rondas intercaladas (base, paralelo, caché, imagen, superficial, todo en cada
ronda). La ronda 1 es de calentamiento para todas; las medianas son de las rondas 2-4. El volumen jk-b-m2 se borra antes de
la ronda 1, así la caché de la ronda 1 es la caché EN FRÍO y se apunta aparte.
Comprueba en cada build: SUCCESS, pruebas (suma de los resúmenes de Surefire), 0 fallos, y que se construyó el .jar.
Escribe ../SALIDA-878.md. Toma el candado <proyecto>/_logs/banco.lock (si lo tiene jk-b ya, no lo vuelve a tomar).

    python velocidad/correr_878.py [--rondas 4] [--solo base,paralelo]
"""
import argparse
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import jk  # noqa: E402

CANDADO = Path(r"<proyecto>\_logs\banco.lock")
SALIDA = AQUI.parent / "SALIDA-878.md"
J = jk.Jenkins("http://localhost:28078")
VARIANTES = ["base", "paralelo", "cache", "imagen", "superficial", "todo"]
md = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    md.append(s)


def sh(c, ok=True):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, MSYS_NO_PATHCONV="1"))
    if ok and r.returncode:
        raise SystemExit(f"falló: {c}\n{r.stdout}\n{r.stderr}")
    return (r.stdout + r.stderr).strip()


RESUMEN = re.compile(r"^\[(?:INFO|WARNING|ERROR)\] Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)\s*$", re.M)


def analizar(nombre, n):
    b = J.esperar(nombre, n, 3600)
    c = J.consola(nombre, n)
    (AQUI / "_consolas").mkdir(exist_ok=True)
    (AQUI / "_consolas" / f"{nombre}-{n}.txt").write_text(c, encoding="utf-8")
    pruebas = [tuple(map(int, m)) for m in RESUMEN.findall(c)]
    run = sum(x[0] for x in pruebas)
    fallos = sum(x[1] + x[2] for x in pruebas)
    salt = sum(x[3] for x in pruebas)
    jar = "Building jar: " in c and "spring-petclinic-4.0.0-SNAPSHOT.jar" in c
    desc = c.count("Downloaded from central")
    mb = 0.0
    for num, uni in re.findall(r"Downloaded from central: \S+ \(([\d.]+) (B|kB|MB)", c):
        mb += float(num) * {"B": 1e-6, "kB": 1e-3, "MB": 1.0}[uni]
    try:
        et = J.etapas(nombre, n)
    except Exception:
        et = []
    return dict(n=n, res=b["result"], dur=b["duration"] / 1000, run=run, fallos=fallos, salt=salt, jar=jar, desc=desc, mb=mb, et=et)


def tomar_candado():
    mio = CANDADO / "dueño-jk-b.txt"
    if CANDADO.exists() and mio.exists():
        return False
    while True:
        try:
            CANDADO.mkdir()
            mio.write_text(f"jk-b (878) {datetime.now(timezone.utc):%FT%TZ}", encoding="utf-8")
            return True
        except FileExistsError:
            print("candado ocupado; espero 30 s", flush=True)
            time.sleep(30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rondas", type=int, default=4)
    ap.add_argument("--solo", default=",".join(VARIANTES))
    a = ap.parse_args()
    variantes = a.solo.split(",")
    tomado = tomar_candado()
    try:
        medir(a.rondas, variantes)
    finally:
        SALIDA.write_text("\n".join(md) + "\n", encoding="utf-8")
        if tomado:
            (CANDADO / "dueño-jk-b.txt").unlink()
            CANDADO.rmdir()
        print("→", SALIDA)


def clonar(extra, veces=5, url="file:///repos/petclinic.git", rama="banco"):
    """git clone dentro de un contenedor de Maven, con los mismos volúmenes que ven los agentes."""
    ts, tam = [], None
    for _ in range(veces):
        guion = (f"cd /tmp && t0=$(date +%s%N) && git clone -q {extra} --branch {rama} {url} pc && "
                 "t1=$(date +%s%N) && echo T=$(( (t1-t0)/1000000 )) && du -sk pc/.git | cut -f1 && git -C pc rev-list --count HEAD")
        r = subprocess.run(["docker", "run", "--rm", "--ulimit", "core=1", "--volumes-from", "jk-b-jenkins-878",
                            "maven:3.9.11-eclipse-temurin-21", "sh", "-c", guion], capture_output=True, text=True,
                           env=dict(os.environ, MSYS_NO_PATHCONV="1"))
        assert r.returncode == 0, r.stderr
        s = r.stdout.strip()
        lin = s.split()
        ts.append(int(lin[0].split("=")[1]) / 1000)
        tam = (int(lin[1]), int(lin[2]))
    return statistics.median(ts), ts, tam


def medir(rondas, variantes):
    p(f"# SALIDA-878 · el pipeline de Spring PetClinic, mejora por mejora\n\n> Corrida {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. "
      "Generado por `velocidad/correr_878.py`. Candado `_logs/banco.lock` tomado.")
    otros = [x for x in sh("docker ps --format {{.Names}}").split() if not x.startswith("jk-b-")]
    p(f"> Otros contenedores vivos al empezar (carga ajena): {', '.join(otros) or 'ninguno'}. "
      f"Docker: {sh('docker info --format {{.NCPU}}')} CPU, {int(sh('docker info --format {{.MemTotal}}')) / 2**30:.1f} GiB.")
    jv = J._req("GET", "/api/json").headers.get("X-Jenkins")
    p(f"> Jenkins {jv} (jk-b-jenkins:2.580.2, plugins fijados), 4 ejecutores en el controlador; agentes `agent {{ docker }}`.")
    p("> Proyecto: spring-petclinic en 500158f7 (2026-09-29; Spring Boot 4.1.0, Java 17) + 1 commit con los Jenkinsfile, rama `banco`, "
      "servido por file:// (sin red). Las dependencias SÍ bajan de Maven Central por internet (lo realista).")
    p("> Las dos pruebas que necesitan Docker (MySqlIntegrationTests, PostgresIntegrationTests) quedan fuera en TODAS las variantes "
      "(-Dtest con exclusión): el agente ve el socket de Docker del controlador y Testcontainers las arrancaba en la máquina.")
    p(f"> Imágenes ya descargadas en local antes de empezar (no se mide su descarga): "
      f"{sh('docker image inspect maven:3.9.11-eclipse-temurin-21 --format {{.Id}}')[:19]} (maven) · "
      f"{sh('docker image inspect jk-b-agente-petclinic:1 --format {{.Id}}')[:19]} (preparada).")

    p("\n## El checkout, aislado (git clone dentro del contenedor de Maven, 5 veces cada uno)")
    for etq, extra in [("completo", ""), ("superficial --depth 1 --no-tags", "--depth 1 --no-tags")]:
        m, ts, (kb, commits) = clonar(extra)
        p(f"- {etq}: mediana {m:.2f} s ({', '.join('%.2f' % t for t in ts)}) · .git {kb / 1024:.1f} MiB · {commits} commits")
    p("- El mismo clone por internet, desde el repositorio público de spring-petclinic (rama main de hoy), 5 veces cada uno:")
    for etq, extra in [("completo", ""), ("superficial --depth 1 --no-tags", "--depth 1 --no-tags")]:
        m, ts, (kb, commits) = clonar(extra, url="https://github.com/spring-projects/spring-petclinic.git", rama="main")
        p(f"- {etq} (internet): mediana {m:.2f} s ({', '.join('%.2f' % t for t in ts)}) · .git {kb / 1024:.1f} MiB · {commits} commits")

    for v in variantes:
        J.crear_pipeline_scm(v, "file:///repos/petclinic.git", "banco", f"jenkins/{v}.Jenkinsfile")
    sh("docker volume rm jk-b-m2", ok=False)
    p("\n- volumen `jk-b-m2` borrado antes de la ronda 1 → la caché de la ronda 1 es EN FRÍO")

    res = {v: [] for v in variantes}
    for r in range(1, rondas + 1):
        p(f"\n## Ronda {r}" + (" (calentamiento; no entra en la mediana)" if r == 1 else ""))
        for v in variantes:
            x = analizar(v, J.lanzar(v))
            res[v].append(x)
            et = " · ".join(f"{nombre} {d:.1f}" for nombre, d, _ in x["et"] if not nombre.startswith("Declarative: Post"))
            p(f"- {v} #{x['n']}: **{x['dur']:.1f} s** {x['res']} · pruebas {x['run']} (fallos {x['fallos']}, saltadas {x['salt']}) · "
              f".jar {'sí' if x['jar'] else 'NO'} · {x['desc']} descargas de Maven Central ({x['mb']:.0f} MB) · etapas: {et}")
            if x["res"] != "SUCCESS" or x["fallos"] or not x["jar"]:
                p("  ⛔ resultado distinto: paro")
                raise SystemExit(1)

    p("\n## ¿Mismo resultado en todas?")
    vistos = {}
    for v in variantes:
        for x in res[v]:
            vistos.setdefault(v, set()).add((x["run"], x["salt"], x["fallos"], x["jar"]))
    for v, s in vistos.items():
        p(f"- {v}: (pruebas, saltadas, fallos, jar) = {sorted(s)}")
    ref = next(iter(vistos.get("base", vistos[variantes[0]])))
    iguales = all(s == {ref} for s in vistos.values())
    p(f"- {'SÍ: las mismas pruebas pasadas y el .jar en todas las variantes' if iguales else 'NO coinciden'}")

    p("\n## Resumen (mediana de las rondas 2-" + str(rondas) + ")")
    base = statistics.median(x["dur"] for x in res["base"][1:]) if "base" in res else None
    for v in variantes:
        ds = [x["dur"] for x in res[v][1:]] or [x["dur"] for x in res[v]]
        m = statistics.median(ds)
        rel = f" · {100 * (m - base) / base:+.0f} % frente a la base" if base else ""
        p(f"- {v}: **{m:.1f} s** ({', '.join('%.1f' % d for d in ds)}){rel} · descargas {statistics.median(x['desc'] for x in res[v][1:] or res[v]):.0f}")
    if "cache" in res:
        c1 = res["cache"][0]
        p(f"- caché EN FRÍO (ronda 1, volumen vacío): {c1['dur']:.1f} s · {c1['desc']} descargas")
    p("\n## Etapas, mediana de las rondas 2-" + str(rondas) + " (s)")
    for v in variantes:
        nombres = [e[0] for e in res[v][-1]["et"]]
        cols = []
        for nom in nombres:
            vals = [d for x in res[v][1:] for (n2, d, _) in x["et"] if n2 == nom]
            if vals:
                cols.append(f"{nom} {statistics.median(vals):.1f}")
        p(f"- {v}: " + " · ".join(cols))


if __name__ == "__main__":
    main()
