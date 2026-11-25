# -*- coding: utf-8 -*-
"""Banco del 877, anexo · ¿por qué el pod-agente tarda ~30 s en irse después del build?

Hipótesis: los contenedores corren `sleep infinity` como PID 1, que no atiende SIGTERM; Kubernetes espera el periodo de
gracia (30 s por defecto) y luego mata con SIGKILL. Prueba: el MISMO pod con terminationGracePeriodSeconds: 3.
5 corridas de cada, en caliente, alternadas. Escribe SALIDA-877-gracia.md. Toma el candado.

    python k8s/correr_877_gracia.py
"""
import statistics
import time
from datetime import datetime, timezone

import correr_877 as K


def main():
    while True:
        try:
            K.CANDADO.mkdir()
            break
        except FileExistsError:
            print("candado ocupado; espero 30 s", flush=True)
            time.sleep(30)
    try:
        medir()
    finally:
        K.CANDADO.rmdir()
        (K.AQUI.parent / "SALIDA-877-gracia.md").write_text("\n".join(K.md) + "\n", encoding="utf-8")


def medir():
    K.p(f"# SALIDA-877-gracia · cuánto tarda en irse el pod-agente\n\n> Corrida {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. "
        "`k8s/correr_877_gracia.py`, candado tomado. En caliente (imágenes ya en el nodo). Alternando las dos variantes.")
    for nom in ["pod-agente", "gracia"]:
        K.J.crear_pipeline(nom, (K.AQUI / "pipelines" / f"{nom}.groovy").read_text(encoding="utf-8"))
    assert not K.pods()
    r = {"pod-agente": [], "gracia": []}
    for i in range(5):
        for nom in r:
            x = K.una_corrida(nom)
            r[nom].append(x)
            K.p(f"- {nom} {i + 1}: build #{x['n']} · espera {x['espera']:.1f} s · pod borrado {x['tras']:.1f} s después del build")
    sale = K.sh(f"kubectl -n {K.NS} get pods") or "No resources found"
    K.p(f"\n- al acabar: {sale}")
    for nom, etq in [("pod-agente", "por defecto (gracia 30 s)"), ("gracia", "terminationGracePeriodSeconds: 3")]:
        K.p(f"- **{etq}**: el pod se va {statistics.median(x['tras'] for x in r[nom]):.1f} s después del build (mediana de 5: "
            f"{', '.join('%.1f' % x['tras'] for x in r[nom])}) · espera de arranque mediana "
            f"{statistics.median(x['espera'] for x in r[nom]):.1f} s")


if __name__ == "__main__":
    main()
