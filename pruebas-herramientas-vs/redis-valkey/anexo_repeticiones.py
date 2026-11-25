# -*- coding: utf-8 -*-
"""anexo_repeticiones.py — ¿la diferencia a tope de SALIDA.md (Redis 305.213 contra Valkey 283.055 op/s sin pipeline, un intento)
es real o es ruido? Repite las cargas a tope 3 veces por variante, alternando el orden, bajo el candado. → ANEXO-repeticiones.md

    python anexo_repeticiones.py
"""
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent))
import correr as R  # noqa: E402
import comun as K  # noqa: E402
from comun import w, num  # noqa: E402

REPES = 3


def main():
    K.red()
    K.OUT.clear()
    res = {}
    with K.candado("redis-valkey anexo"):
        w("# ANEXO — repeticiones de la carga a tope (Redis contra Valkey)\n")
        w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}, bajo el candado. Mismo montaje que SALIDA.md; cada variante {REPES} veces, "
          "orden alternado (ida y vuelta), contenedor nuevo y el millón de claves cargado cada vez.\n")
        orden = R.VARIANTES
        for i in range(REPES):
            for k, io in (orden if i % 2 == 0 else list(reversed(orden))):
                for pipe in (1, 16):
                    R.arrancar(k, io)
                    R.pong(time.perf_counter())
                    R.cargar_claves()
                    R.memtier(R.mezcla(pipe), seg=R.SEG_CAL)
                    r = R.memtier(R.mezcla(pipe))
                    K.rm("kv")
                    res.setdefault((k, io, pipe), []).append(r["ops"])
                    print(k, io, pipe, r["ops"], flush=True)
        for pipe in (1, 16):
            w(f"## Pipeline {pipe} · 1 SET por cada 10 GET · operaciones/s\n")
            w("| servidor | intento 1 | intento 2 | intento 3 | mediana | mín–máx |")
            w("|---|---|---|---|---|---|")
            for k, io in orden:
                xs = res[(k, io, pipe)]
                w(f"| {R.nv(k, io)} | " + " | ".join(num(x, 0) for x in xs) + f" | {num(statistics.median(xs), 0)} | "
                  f"{num(min(xs), 0)}–{num(max(xs), 0)} |")
            w()
    K.guardar(AQUI / "ANEXO-repeticiones.md")


if __name__ == "__main__":
    main()
