# -*- coding: utf-8 -*-
"""Banco del 877, anexo · la consola completa de un build en caliente y el pod visto desde kubectl mientras vive.
Sin cronómetro (no toma el candado). Escribe SALIDA-877-consola.md.

    python k8s/consola_877.py
"""
import subprocess
import threading
import time

import correr_877 as K


def main():
    K.J.crear_pipeline("pod-agente", (K.AQUI / "pipelines" / "pod-agente.groovy").read_text(encoding="utf-8"))
    vistas = []
    fin = threading.Event()

    def mirar():
        while not fin.is_set():
            s = K.sh(f"kubectl -n {K.NS} get pods --no-headers", ok=False)
            if s and (not vistas or vistas[-1][1] != s):
                vistas.append((time.strftime("%H:%M:%S"), s))
            time.sleep(0.5)

    h = threading.Thread(target=mirar, daemon=True)
    h.start()
    n = K.J.lanzar("pod-agente")
    b = K.J.esperar("pod-agente", n, 600)
    K.esperar_sin_pods(90)
    time.sleep(1)
    fin.set()
    h.join()
    cons = K.J.consola("pod-agente", n)
    out = [f"# SALIDA-877-consola · un build de pod-agente en caliente (build #{n}, {b['result']}, {b['duration'] / 1000:.1f} s)\n",
           "`k8s/consola_877.py`. Sin cronómetro.\n", "## La consola del build\n```", cons.rstrip(), "```\n",
           f"## `kubectl -n {K.NS} get pods` cada medio segundo (solo cuando cambia)\n```"]
    for t, s in vistas:
        out.append(f"[{t}]\n{s}")
    out.append("```")
    (K.AQUI.parent / "SALIDA-877-consola.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[-12:]))


if __name__ == "__main__":
    main()
