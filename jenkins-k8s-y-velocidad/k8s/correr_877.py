# -*- coding: utf-8 -*-
"""Banco del 877 · Jenkins en Kubernetes: cada build en su propio pod.

Requiere: crear_cluster.sh (kind jk-b-k8s en la red jk-b-net) y levantar_877.sh (controlador jk-b-jenkins-877, puerto 28077).
Escribe SALIDA-877.md al lado del banco. Toma el candado <proyecto>/_logs/banco.lock mientras mide (si existe, espera).

    python k8s/correr_877.py
"""
import json
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

KCFG = str(AQUI / "kubeconfig")
NS = "jenkins-agentes"
NODO = "jk-b-k8s-control-plane"
CANDADO = Path(r"<proyecto>\_logs\banco.lock")
SALIDA = AQUI.parent / "SALIDA-877.md"
IMAGENES = ["docker.io/library/maven:3.9.11-eclipse-temurin-21", "docker.io/library/node:22.21.1-alpine",
            "docker.io/jenkins/inbound-agent:3391.va_37fa_a_305d6d-1-jdk25"]
J = jk.Jenkins("http://localhost:28077")
md = []


def sh(c, ok=True):
    env = dict(os.environ, KUBECONFIG=KCFG, MSYS_NO_PATHCONV="1")
    r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
    if ok and r.returncode:
        raise SystemExit(f"falló: {c}\n{r.stdout}\n{r.stderr}")
    return (r.stdout + r.stderr).strip()


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    md.append(s)


def bloque(titulo, texto):
    p(f"\n`$ {titulo}`\n```\n{texto}\n```")


def pods():
    return json.loads(sh(f"kubectl -n {NS} get pods -o json"))["items"]


def esperar_sin_pods(tope=60):
    t0 = time.time()
    while time.time() - t0 < tope:
        if not pods():
            return time.time() - t0
        time.sleep(0.5)
    return None


def eventos(pod):
    ev = json.loads(sh(f"kubectl -n {NS} get events -o json"))["items"]
    return [e for e in ev if e["involvedObject"].get("name") == pod]


def una_corrida(nombre):
    n = J.lanzar(nombre)
    b = J.esperar(nombre, n, 900)
    txt = J.consola(nombre, n)
    m = re.search(r"T_AGENTE=(\d+) INICIO=(\d+) POD=(\S+)", txt)
    assert b["result"] == "SUCCESS" and m, (nombre, n, b["result"], txt[-1500:])
    espera = (int(m.group(1)) - int(m.group(2))) / 1000
    mvn = re.search(r"Apache Maven (\S+)", txt).group(1)
    nodev = re.search(r"^(v\d+\.\d+\.\d+)$", txt, re.M).group(1)
    pod = m.group(3)
    tras = esperar_sin_pods()
    ev = eventos(pod)
    tirones = [e["message"] for e in ev if e["reason"] == "Pulled"]
    return dict(n=n, espera=espera, total=b["duration"] / 1000, pod=pod, mvn=mvn, node=nodev, tras=tras, tirones=tirones)


def lista(rs):
    return ", ".join("%.1f" % r["espera"] for r in rs)


def quitar_imagenes_del_nodo():
    for im in IMAGENES:
        sh(f"docker exec {NODO} crictl rmi {im}", ok=False)
    quedan = sh(f"docker exec {NODO} crictl images").splitlines()
    for im in IMAGENES:
        repo, tag = im.rsplit(":", 1)
        assert not any(ln.split()[:2] == [repo, tag] for ln in quedan), quedan


def main():
    while True:
        try:
            CANDADO.mkdir()
            break
        except FileExistsError:
            print("candado ocupado; espero 30 s", flush=True)
            time.sleep(30)
    try:
        medir()
    finally:
        CANDADO.rmdir()
        SALIDA.write_text("\n".join(md) + "\n", encoding="utf-8")
        print("→", SALIDA)


def medir():
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    p(f"# SALIDA-877 · Jenkins en Kubernetes: agentes como pods\n\n> Corrida {ahora}. Generado por `k8s/correr_877.py`. "
      "Candado `_logs/banco.lock` tomado durante toda la corrida.")
    otros = sh("docker ps --format '{{.Names}}'")
    p(f"> Otros contenedores vivos en la máquina al empezar (carga ajena): {', '.join(x for x in otros.split() if not x.startswith('jk-b-')) or 'ninguno'}")
    p(f"> Docker: {sh('docker info --format {{.NCPU}}')} CPU, {int(sh('docker info --format {{.MemTotal}}')) / 2**30:.1f} GiB.")

    p("\n## Versiones")
    ver = J.json("/api/json?tree=nodeName")
    jv = J._req("GET", "/api/json").headers.get("X-Jenkins")
    plug = {x["shortName"]: x["version"] for x in J.json("/pluginManager/api/json?depth=1&tree=plugins[shortName,version]")["plugins"]}
    p(f"- Jenkins {jv} (imagen jk-b-jenkins:2.580.2, {len(plug)} plugins fijados) · plugin kubernetes {plug['kubernetes']}")
    p(f"- {sh('kind version')} · nodo {sh('kubectl get nodes -o jsonpath={.items[0].status.nodeInfo.kubeletVersion}')} "
      f"({sh('kubectl get nodes -o jsonpath={.items[0].status.nodeInfo.containerRuntimeVersion}')})")
    p(f"- Nodo asignable: {sh('kubectl get nodes -o jsonpath={.items[0].status.allocatable.cpu}')} CPU · "
      f"{sh('kubectl get nodes -o jsonpath={.items[0].status.allocatable.memory}')} de memoria")
    del ver

    for nom in ["pod-agente", "ocupado", "pendiente", "oom"]:
        J.crear_pipeline(nom, (AQUI / "pipelines" / f"{nom}.groovy").read_text(encoding="utf-8"))
    assert not pods(), "quedaban pods de antes"

    # ── 1 · arranque en frío: el nodo no tiene ninguna de las tres imágenes ──
    p("\n## 1 · Arranque de un pod-agente en FRÍO (el nodo no tiene las imágenes; `crictl rmi` antes de cada corrida)")
    p("Espera = del inicio del build al primer `sh` dentro del pod (reloj del contenedor contra `startTimeInMillis`; "
      "mismo núcleo, misma hora).")
    frio = []
    for i in range(3):
        quitar_imagenes_del_nodo()
        r = una_corrida("pod-agente")
        frio.append(r)
        p(f"- frío {i + 1}: build #{r['n']} · espera {r['espera']:.1f} s · build entero {r['total']:.1f} s · "
          f"pod borrado {r['tras']:.1f} s después · Maven {r['mvn']} · Node {r['node']}")
        for t in r["tirones"]:
            p(f"    - kubelet: {t}")
    # ── 2 · en caliente ──
    p("\n## 2 · Arranque de un pod-agente en CALIENTE (las imágenes ya están en el nodo)")
    cal = []
    for i in range(5):
        r = una_corrida("pod-agente")
        cal.append(r)
        p(f"- caliente {i + 1}: build #{r['n']} · espera {r['espera']:.1f} s · build entero {r['total']:.1f} s · "
          f"pod borrado {r['tras']:.1f} s después · Maven {r['mvn']} · Node {r['node']}")
        for t in r["tirones"]:
            p(f"    - kubelet: {t}")

    p("\n## ¿Mismo resultado en todas las corridas?")
    salidas = {(r["mvn"], r["node"]) for r in frio + cal}
    p(f"- versiones vistas dentro del pod: {salidas} → {'SÍ, idénticas' if len(salidas) == 1 else 'NO'}")
    assert len(salidas) == 1
    nombres = [r["pod"] for r in frio + cal]
    p(f"- pods distintos: {len(set(nombres))} de {len(nombres)} builds (uno nuevo por build)")
    p(f"- pods que quedan en `{NS}` al acabar cada build: 0 en las {len(nombres)} corridas")

    mf, mc = statistics.median(r["espera"] for r in frio), statistics.median(r["espera"] for r in cal)
    p("\n## Resumen del arranque")
    p(f"- FRÍO   mediana de 3: **{mf:.1f} s** (corridas: {lista(frio)})")
    p(f"- CALIENTE mediana de 5: **{mc:.1f} s** (corridas: {lista(cal)})")
    p(f"- build entero (3 etapas cortas): frío {statistics.median(r['total'] for r in frio):.1f} s · "
      f"caliente {statistics.median(r['total'] for r in cal):.1f} s")

    # ── 3 · tres builds a la vez ──
    p("\n## 3 · Tres builds a la vez (job `ocupado`: el mismo pod, 25 s de trabajo)")
    ns = [J.lanzar("ocupado") for _ in range(3)]
    t0 = time.time()
    while time.time() - t0 < 120:
        corriendo = [x for x in pods() if x["status"].get("phase") == "Running"]
        if len(corriendo) >= 3:
            break
        time.sleep(1)
    time.sleep(3)
    bloque(f"kubectl get pods -n {NS}", sh(f"kubectl -n {NS} get pods"))
    bloque("kubectl describe node | (recursos asignados)",
           "\n".join(sh("kubectl describe node").split("Allocated resources:")[1].split("Events:")[0].strip().splitlines()[:6]))
    reqs = [(c["name"], c.get("resources", {}).get("requests", {})) for c in pods()[0]["spec"]["containers"]]
    p(f"- peticiones de UN pod-agente: {reqs}")
    res = [J.esperar("ocupado", n, 300)["result"] for n in ns]
    p(f"- resultado de los tres: {res}")
    t = esperar_sin_pods()
    bloque(f"kubectl get pods -n {NS}   # al terminar", sh(f"kubectl -n {NS} get pods") or "No resources found in jenkins-agentes namespace.")
    p(f"- los tres pods desaparecieron {t:.1f} s después del último build")

    # ── 4 · el pod pide más de lo que hay ──
    p("\n## 4 · Un pod que pide 32 CPU en un nodo con 24 (job `pendiente`)")
    n = J.lanzar("pendiente")
    t0 = time.time()
    tope = 300
    while time.time() - t0 < tope:
        b = J.json(f"/job/pendiente/{n}/api/json?tree=building,result")
        if not b["building"]:
            break
        time.sleep(5)
    seguia = J.json(f"/job/pendiente/{n}/api/json?tree=building,result")
    p(f"- a los {time.time() - t0:.0f} s: building={seguia['building']} result={seguia['result']}")
    bloque(f"kubectl get pods -n {NS}", sh(f"kubectl -n {NS} get pods"))
    fs = [e for e in json.loads(sh(f"kubectl -n {NS} get events -o json"))["items"] if e["reason"] == "FailedScheduling"]
    if fs:
        p(f"- evento FailedScheduling (×{fs[-1].get('count') or 1}): {fs[-1]['message']}")
    cons = J.consola("pendiente", n)
    p(f"- la consola repite «Still waiting to schedule task» {cons.count('Still waiting to schedule task')} veces")
    bloque("consola del build (extracto)", "\n".join(ln for ln in cons.splitlines() if "Unschedulable" in ln or "Created Pod" in ln)[:600])
    if seguia["building"]:
        J.abortar("pendiente", n)
        J.esperar("pendiente", n, 120)
    t = esperar_sin_pods(180)
    if t is not None:
        p(f"- tras abortarlo a mano, el pod Pending se borró en {t:.1f} s")
    else:
        bloque(f"kubectl get pods -n {NS}   # 180 s después de abortar", sh(f"kubectl -n {NS} get pods"))
        p("- 180 s después de abortar el build, el pod Pending SEGUÍA ahí: lo borro a mano con kubectl delete pod")
        for x in pods():
            sh(f"kubectl -n {NS} delete pod {x['metadata']['name']}")

    # ── 5 · OOM ──
    p("\n## 5 · Un contenedor con límite de 128 MiB que reserva 300 MiB (job `oom`)")
    resultados = []
    for i in range(3):
        n = J.lanzar("oom")
        t0 = time.time()
        b = J.esperar("oom", n, 900)
        cons = J.consola("oom", n)
        lineas = [ln.strip() for ln in cons.splitlines() if any(k in ln for k in ("OOMKilled", "terminated (", "Agent was removed",
                                                                                     "was deleted", "Finished:"))]
        resultados.append(b["result"])
        p(f"- oom {i + 1}: build #{n} → **{b['result']}** en {b['duration'] / 1000:.1f} s")
        if i == 0:
            bloque("consola del build (líneas clave)", "\n".join(dict.fromkeys(lineas)))
        esperar_sin_pods()
    p(f"- resultados: {resultados}")

    p("\n## Lo que queda en el clúster")
    bloque(f"kubectl get pods -n {NS}", sh(f"kubectl -n {NS} get pods") or "No resources found in jenkins-agentes namespace.")


if __name__ == "__main__":
    main()
