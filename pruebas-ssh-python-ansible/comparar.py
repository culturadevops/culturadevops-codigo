# -*- coding: utf-8 -*-
"""¿LLEGARON LOS DOS AL MISMO ESTADO? flota.py (asyncssh) y ansible-playbook sobre los 50, host por host.
Antes de comparar nada (líneas, tiempos), los dos tienen que ver lo mismo: los mismos ok, el mismo código y la misma salida.
Si no coinciden, sale con 1. Ansible deja un JSON por host con el callback «tree» (viene con ansible-core)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ARBOL = Path("/root/arbol")
shutil.rmtree(ARBOL, ignore_errors=True)

f = subprocess.run(["python", "flota.py", "-hosts", "hosts-50.txt", "-p", "50", "-json"], capture_output=True, text=True)
py = {r["host"]: r for r in json.loads(f.stdout)}

env = {**os.environ, "ANSIBLE_CALLBACKS_ENABLED": "tree", "ANSIBLE_CALLBACK_TREE_DIR": str(ARBOL)}
subprocess.run(["ansible-playbook", "revisar.yml", "-f", "50", "-T", "3"], capture_output=True, text=True, env=env)
an = {p.name: json.loads(p.read_text()) for p in ARBOL.iterdir()}


def estado_py(r):
    # raw de Ansible pide terminal (-tt): stderr llega mezclado en stdout. Para comparar, se juntan aquí también.
    if r["rc"] is None:
        return ("error", None, "")
    return ("ok", r["rc"], "\n".join(x for x in (r["out"], r["err"]) if x))


def estado_an(r):
    if r.get("unreachable") or "rc" not in r:
        return ("error", None, "")
    return ("ok", r["rc"], r.get("stdout", "").replace("\r\n", "\n").strip())


distintos = 0
cuenta = {"python": {}, "ansible": {}}
for h in sorted(py):
    a, b = estado_py(py[h]), estado_an(an.get(h, {}))
    for lado, e in (("python", a), ("ansible", b)):
        clave = "error" if e[0] == "error" else f"rc={e[1]}"
        cuenta[lado][clave] = cuenta[lado].get(clave, 0) + 1
    if a != b:
        distintos += 1
        print(f"DISTINTO {h}: python={a} ansible={b}")
        print(f"   ansible dijo: {json.dumps(an.get(h), ensure_ascii=False)[:300]}")
print("python :", dict(sorted(cuenta["python"].items())))
print("ansible:", dict(sorted(cuenta["ansible"].items())))
print(f"hosts con el mismo estado y la misma salida: {50 - distintos} de 50")
sys.exit(1 if distintos else 0)
