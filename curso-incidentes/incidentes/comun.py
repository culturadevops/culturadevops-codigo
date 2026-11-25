# -*- coding: utf-8 -*-
"""Lo que comparten los incidentes: consultar Prometheus y Loki por su API, leer el «busca»
(las alertas que llegan), generar tráfico y llevar la línea de tiempo del postmortem.

Todo lo que se imprime sale de una consulta o de una medición: nada escrito de antemano.
"""
import json
import os
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
PROM = "http://127.0.0.1:19090"
LOKI = "http://127.0.0.1:13100"
TIENDA = "http://127.0.0.1:18000"
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def titulo(t):
    print(f"\n== {t} ==", flush=True)


def docker(*args, check=True):
    r = subprocess.run(["docker", "compose", *args], cwd=AQUI, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode != 0:
        raise SystemExit(f"docker compose {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def _get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def prom(q):
    """Una consulta instantánea de PromQL. Devuelve [(etiquetas, valor)]."""
    d = _get(f"{PROM}/api/v1/query?" + urllib.parse.urlencode({"query": q}))
    return [(x["metric"], float(x["value"][1])) for x in d["data"]["result"]]


def prom1(q, defecto=None):
    r = prom(q)
    return r[0][1] if r else defecto


def loki(q, desde, limite=5):
    """Las últimas líneas de LogQL desde `desde` (epoch). Devuelve [(hora, línea)]."""
    d = _get(f"{LOKI}/loki/api/v1/query_range?" + urllib.parse.urlencode(
        {"query": q, "start": str(int(desde * 1e9)), "limit": limite, "direction": "backward"}))
    out = []
    for s in d["data"]["result"]:
        out += [(int(t) / 1e9, l) for t, l in s["values"]]
    return sorted(out)[-limite:]


def busca(desde):
    """Las alertas que han llegado al «busca» desde `desde`: [(t, estado, alerta, resumen)]."""
    out = []
    for l in docker("logs", "--no-log-prefix", "receptor").splitlines():
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if d["t"] >= desde:
            out.append((d["t"], d["estado"], d["alerta"], d["resumen"]))
    return out


def esperar_alerta(alerta, desde, estado="firing", limite=240):
    t_fin = time.time() + limite
    while time.time() < t_fin:
        for t, e, a, _ in busca(desde):
            if a == alerta and e == estado:
                return t
        time.sleep(1)
    # Sin alerta no hay incidente que contar: se para aquí, a la vista, en vez de seguir como si nada.
    raise SystemExit(f"[X] la alerta {alerta} no llegó ({estado}) en {limite} s")


def esperar_tienda(url=TIENDA, limite=60):
    for _ in range(limite * 2):
        try:
            urllib.request.urlopen(url + "/salud", timeout=1).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


class Trafico:
    """Clientes pidiendo sin parar. Cuenta los resultados: código HTTP o el error de red."""

    def __init__(self, url, hilos=4, pausa=0.1, timeout=5):
        self.url, self.hilos, self.pausa, self.timeout = url, hilos, pausa, timeout
        self.res = Counter()
        self._fin = threading.Event()
        self._candado = threading.Lock()

    def _uno(self):
        while not self._fin.is_set():
            try:
                with urllib.request.urlopen(self.url, timeout=self.timeout) as r:
                    r.read()
                    clave = str(r.status)
            except urllib.error.HTTPError as e:
                clave = str(e.code)
            except Exception as e:
                clave = type(getattr(e, "reason", e)).__name__
            with self._candado:
                self.res[clave] += 1
            time.sleep(self.pausa)

    def __enter__(self):
        self._ts = [threading.Thread(target=self._uno, daemon=True) for _ in range(self.hilos)]
        for t in self._ts:
            t.start()
        return self

    def __exit__(self, *a):
        self._fin.set()
        for t in self._ts:
            t.join(timeout=self.timeout + 2)

    def resumen(self):
        with self._candado:
            return ", ".join(f"{k}: {v}" for k, v in sorted(self.res.items()))


class Cronologia:
    """La línea de tiempo del incidente, en segundos desde que empezó. Va al postmortem."""

    def __init__(self):
        self.t0 = time.time()
        self.eventos = []

    def marca(self, texto, t=None):
        s = (t or time.time()) - self.t0
        self.eventos.append((s, texto))
        print(f"  [{s:6.1f} s] {texto}", flush=True)
        return s

    def desde(self, texto):
        return next(s for s, t in self.eventos if t.startswith(texto))


def postmortem(num, titulo_, cron, resumen, causa, bien, mal, acciones, desde=None):
    """Escribe postmortems/NN.md con el formato sin culpables y lo dice.

    `desde`: el evento con el que empieza el incidente de verdad (por defecto, el primero). Las
    alertas de ANTES no cuentan como detección: son avisos previos."""
    ini = cron.desde(desde) if desde else cron.eventos[0][0]
    det = next((s for s, t in cron.eventos if t.startswith("ALERTA") and s >= ini), None)
    mit = next((s for s, t in cron.eventos if t.startswith("MITIGADO") and s >= ini), None)
    lineas = [f"# Postmortem {num:02d} · {titulo_}", "", "_Sin culpables: se buscan causas y defensas, no nombres._", "",
              "## Resumen", resumen, "",
              "## Los números",
              f"- Detección: {det - ini:.0f} s desde que empezó" if det is not None else "- Detección: no hubo alerta",
              f"- Mitigación: {mit - ini:.0f} s desde que empezó" if mit is not None else "- Mitigación: -", "",
              "## Línea de tiempo", *[f"- `{s:6.1f} s` {t}" for s, t in cron.eventos], "",
              "## Causa", causa, "",
              "## Qué funcionó", *[f"- {x}" for x in bien], "",
              "## Qué no", *[f"- {x}" for x in mal], "",
              "## Acciones", *[f"- [ ] {x}" for x in acciones], ""]
    destino = AQUI / "postmortems" / f"{num:02d}.md"
    destino.write_text("\n".join(lineas), encoding="utf-8", newline="\n")
    print(f"  -> postmortem escrito: postmortems/{destino.name}"
          f" (detección {det - ini:.0f} s · mitigación {mit - ini:.0f} s)" if det is not None and mit is not None
          else f"  -> postmortem escrito: postmortems/{destino.name}")
