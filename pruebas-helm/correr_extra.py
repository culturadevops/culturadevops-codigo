# -*- coding: utf-8 -*-
"""Segunda parte del banco del 407 (Helm): lint y template sin clúster, el chart en un registro OCI, y valores.
Aparte de correr.py para no cambiar los hashes ya copiados al guion. Necesita k3s y herr (de correr.py).
    python correr_extra.py   -> SALIDA-extra.md
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "herr", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n")
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    run(["docker", "rm", "-f", "registro"])
    run(["docker", "run", "-d", "--name", "registro", "--network", "lab-k8s", "registry:3"])
    OUT.append(f"# SALIDA (2.ª parte) — Helm 4 (vídeo 407)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`.\n")

    OUT.append("## 7 · Ver lo que se va a aplicar, sin clúster\n")
    ex("cd /tmp && rm -rf demo && helm4 create demo >/dev/null")
    bloque("lint", "helm4 lint demo", "cd /tmp && helm4 lint demo")
    bloque("un error en el chart", "(replicaCount: \"tres\") helm4 lint demo",
           "cd /tmp && cp -r demo roto && sed -i 's/^replicaCount: 1/replicaCount: tres: x/' roto/values.yaml && helm4 lint roto 2>&1 | tail -3")
    bloque("template: los manifiestos, sin aplicar nada", "helm4 template web ./demo | grep -E '^kind:' | sort | uniq -c",
           "cd /tmp && helm4 template web ./demo | grep -E '^kind:' | sort | uniq -c")

    OUT.append("## 8 · El chart en un registro OCI\n")
    bloque("empaquetar y subir", "helm4 push demo-0.1.0.tgz oci://registro:5000/charts --plain-http",
           "cd /tmp && helm4 package demo -d oci >/dev/null && helm4 push oci/demo-0.1.0.tgz oci://registro:5000/charts --plain-http 2>&1")
    bloque("leerlo desde el registro", "helm4 show chart oci://registro:5000/charts/demo --plain-http",
           "helm4 show chart oci://registro:5000/charts/demo --version 0.1.0 --plain-http 2>&1 | grep -E '^(name|version|appVersion)'")
    bloque("instalarlo desde ahí, con un valor cambiado", "helm4 install web oci://registro:5000/charts/demo --set replicaCount=2 …",
           "helm4 install web oci://registro:5000/charts/demo --version 0.1.0 --plain-http -n oci --create-namespace --set replicaCount=2 --wait 2>&1 | grep -E 'STATUS|REVISION'; "
           "kubectl get deploy web-demo -n oci -o jsonpath='réplicas={.spec.replicas}'")
    bloque("qué valores cambié", "helm4 get values web -n oci", "helm4 get values web -n oci")
    ex("helm4 uninstall web -n oci >/dev/null")

    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    run(["docker", "rm", "-f", "registro"])
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
