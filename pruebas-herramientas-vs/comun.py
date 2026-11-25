# -*- coding: utf-8 -*-
"""comun.py — piezas compartidas de los bancos «¿X o Y? Lo medí» de HERRAMIENTAS (cultura-devops 836-840, pedido del dueño
2026-11-05: llevar la serie de lenguajes a herramientas de DevOps con el mismo rigor).

Reglas de todos los bancos de esta carpeta:
  · imágenes OFICIALES con versión fijada; el servidor medido limitado a 2 CPU y 1 GiB;
  · la carga sale de OTRO contenedor (wrk, hey, sysbench, memtier) en la misma red de Docker;
  · antes de medir, comprobación de que los dos lados hacen lo mismo y devuelven lo mismo (si no, exit 1);
  · `docker run --rm` SIEMPRE y los volúmenes con nombre se borran al terminar;
  · todo cronometraje va bajo el candado _logs/banco.lock (en la máquina se renderiza y otros agentes miden).
"""
import io
import os
import re
import statistics
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

AQUI = Path(__file__).resolve().parent
LOCK = Path(r"<proyecto>\_logs\banco.lock")
RED = "hvs"
CPUS, MEM = "2", "1g"
OUT = []


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ok(args, **kw):
    r = sh(args, **kw)
    if r.returncode != 0:
        raise SystemExit(f"⛔ falló: {' '.join(map(str, args))}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


def w(s=""):
    print(s, flush=True)
    OUT.append(s)


def guardar(ruta):
    Path(ruta).write_text("\n".join(OUT) + "\n", encoding="utf-8")
    print(f"\n[ok] {ruta}")


@contextmanager
def candado(quien):
    """mkdir atómico; si otro lo tiene, espera de 60 en 60 s. Se suelta SIEMPRE al salir (rm -rf)."""
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            try:
                d = (LOCK / "dueño.txt").read_text(encoding="utf-8").strip()
            except Exception:
                d = "?"
            print(f"[candado] ocupado por «{d}» — espero 60 s ({datetime.now():%H:%M})", flush=True)
            time.sleep(60)
    (LOCK / "dueño.txt").write_text(f"agente herramientas-vs ({quien}) pid {os.getpid()} desde {datetime.now():%Y-%m-%d %H:%M}\n",
                                    encoding="utf-8")
    try:
        yield
    finally:
        sh(["cmd", "/c", "rmdir", "/s", "/q", str(LOCK)])
        if LOCK.exists():
            import shutil
            shutil.rmtree(LOCK, ignore_errors=True)
        print("[candado] suelto", flush=True)


def red():
    sh(["docker", "network", "create", RED])


def rm(*nombres):
    for n in nombres:
        sh(["docker", "rm", "-f", n])


def tam_imagen(img):
    return int(ok(["docker", "image", "inspect", "-f", "{{.Size}}", img]).stdout.strip()) / 1048576


def a_mib(s):
    s = s.strip()
    v = float(re.match(r"[\d.]+", s).group(0))
    if "KiB" in s or "kB" in s:
        return v / 1024
    if "GiB" in s or "GB" in s:
        return v * 1024
    if s.endswith("B") and "MiB" not in s and "MB" not in s:
        return v / 1048576
    return v


def stats(nombre):
    """(MiB, %CPU) de docker stats, una muestra."""
    r = sh(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}|{{.CPUPerc}}", nombre]).stdout.strip()
    m, c = r.split("|")
    return a_mib(m.split("/")[0]), float(c.strip().rstrip("%"))


class Muestreo:
    """Muestrea memoria y CPU de un contenedor mientras dura el bloque `with`."""

    def __init__(self, nombre):
        self.nombre, self.mem, self.cpu = nombre, [], []
        self._fin = threading.Event()

    def _bucle(self):
        while not self._fin.is_set():
            try:
                m, c = stats(self.nombre)
                self.mem.append(m)
                self.cpu.append(c)
            except Exception:
                pass

    def __enter__(self):
        self._th = threading.Thread(target=self._bucle, daemon=True)
        self._th.start()
        return self

    def __exit__(self, *a):
        self._fin.set()
        self._th.join()

    @property
    def mem_max(self):
        return max(self.mem) if self.mem else float("nan")

    @property
    def cpu_media(self):
        # la primera muestra de docker stats a veces sale en 0: se descarta si hay más
        c = self.cpu[1:] if len(self.cpu) > 2 else self.cpu
        return statistics.mean(c) if c else float("nan")


def ms(valor, unidad):
    return float(valor) * {"us": 0.001, "µs": 0.001, "ms": 1.0, "s": 1000.0}[unidad]


def mediana(xs):
    return statistics.median(xs)


def num(x, dec=1):
    """Número a la española para las tablas: 1.234,5"""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")
