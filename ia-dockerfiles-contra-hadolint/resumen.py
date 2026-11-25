# -*- coding: utf-8 -*-
"""Cuenta resultados.json (+ las referencias) y escribe SALIDA.md. Todas las cifras del vídeo 711 salen de aquí."""
import collections
import glob
import json
import os
import statistics
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
LENG = {"n": "Node", "p": "Python", "g": "Go", "j": "Java"}


def med(xs):
    return round(statistics.median(xs), 1) if xs else None


def tabla_medidas(L, filas):
    L.append("| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for app, m in filas:
        codes = ",".join(sorted({a["code"] for a in m["hadolint"]}))
        L.append(f"| {app} | {len(m['hadolint'])} {codes} | {'sí' if m['construye'] else 'NO'} | {'sí' if m.get('arranca') else '—' if not m['construye'] else 'NO'} | "
                 f"{m.get('disco_mb', '')} | {m.get('usuario', '')} | {m.get('root', '')} | {m['latest']} | {' '.join(m['bases'])} |")


def bloque(quien, por_app, L):
    n = len(por_app)
    r0 = {a: rs[0]["medida"] for a, rs in por_app.items()}
    fin = {a: rs[-1]["medida"] for a, rs in por_app.items()}
    con_av = [a for a, rs in por_app.items() if rs[0]["hadolint"]]
    cod = collections.Counter(x["code"] for rs in por_app.values() for x in rs[0]["hadolint"])
    L.append(f"\n## {quien} — {n} apps\n")
    L.append(f"- Ronda 0 con al menos un aviso de hadolint: **{len(con_av)} de {n}**; avisos: {sum(cod.values())} · por código: {dict(cod.most_common())}")
    for et, d in (("Ronda 0", r0), ("Última ronda", fin)):
        cons = [a for a, m in d.items() if m["construye"]]
        arr = [a for a, m in d.items() if m.get("arranca")]
        root = [a for a, m in d.items() if m["construye"] and m["root"]]
        lat = [a for a, m in d.items() if m["latest"]]
        L.append(f"- {et}: construyen {len(cons)}/{n} · arrancan y responden {len(arr)}/{n} · corren como root {len(root)} de {len(cons)} construidas "
                 f"{root} · usan latest {len(lat)} {lat}")
        L.append(f"  - No construyen: {[a for a in d if a not in cons]}")
        L.append(f"  - Construyen y no arrancan: {[a for a in cons if a not in arr]}")
        por_l = collections.defaultdict(list)
        for a, m in d.items():
            if m["construye"]:
                por_l[LENG[a[0]]].append(m["disco_mb"])
        L.append("  - Disco (MB), mediana por lenguaje: " + ", ".join(f"{l} {med(v)} (n={len(v)})" for l, v in por_l.items()))
    bases = collections.Counter(b for m in r0.values() for b in m["bases"])
    L.append(f"- Imágenes base en ronda 0: {dict(bases.most_common())}")
    if con_av:
        hasta = collections.Counter()
        for a in con_av:
            rs = por_app[a]
            k = next((r["k"] for r in rs if not r["hadolint"]), None)
            hasta["nunca (3 rondas)" if k is None else f"limpio en ronda {k}"] += 1
        L.append(f"- Bucle IA + hadolint sobre {len(con_av)}: {dict(sorted(hasta.items()))}")
        supr = [(a, rs[-1]["supr"] - rs[0]["supr"]) for a, rs in por_app.items() if rs[-1]["supr"] > rs[0]["supr"]]
        L.append(f"- Supresiones nuevas (# hadolint ignore): {supr or 'ninguna'}")
        cambios = []
        for a in con_av:
            m0, mf = r0[a], fin[a]
            cambios.append(f"{a}: construye {m0['construye']}→{mf['construye']}, arranca {m0.get('arranca')}→{mf.get('arranca')}, "
                           f"root {m0.get('root')}→{mf.get('root')}, disco {m0.get('disco_mb')}→{mf.get('disco_mb')}")
        L.append("- Antes → después del bucle:\n  - " + "\n  - ".join(cambios))
    L.append("\n### Ronda 0\n")
    tabla_medidas(L, sorted(r0.items()))
    L.append("\n### Última ronda\n")
    tabla_medidas(L, sorted(fin.items()))


def main():
    with open(os.path.join(AQUI, "resultados.json"), encoding="utf-8") as f:
        res = json.load(f)
    tags = json.loads(subprocess.run(["curl", "-s", "http://127.0.0.1:11434/api/tags"], capture_output=True, text=True).stdout)
    dg = next((m["digest"] for m in tags["models"] if m["name"] == "qwen2.5:7b"), "?")
    costo, segs, modelos = 0.0, [], set()
    for f in glob.glob(os.path.join(AQUI, "muestras", "claude", "*", "r*.json")):
        if f.endswith((".hadolint.json", ".medida.json")):
            continue
        j = json.load(open(f, encoding="utf-8"))
        costo += j.get("costo_usd") or 0
        modelos.update(j.get("modelos", []))
        if f.endswith("r0.json"):
            segs.append(j.get("segundos") or 0)
    import generar
    flags = " ".join(a or '""' for a in generar.CLAUDE_FLAGS)
    L = ["# SALIDA — 711 · Dockerfiles escritos por IA contra hadolint (y lo que pesan)", "",
         "Generado por `resumen.py` (`crear_apps.py` → `generar.py` → `analizar.py` → `resumen.py`; `ejecutar_todo.py` lo corre todo). "
         "Medido el 2026-10-29. **No es un estudio**: 20 apps, un modelo local y Claude Code.", "", "## Montaje", "",
         "- 20 apps fijadas antes de generar (crear_apps.py): 5 Node, 5 Python, 5 Go, 5 Java. Todas escuchan en 8080 y responden «ok».",
         f"- qwen2.5:7b por Ollama, digest `{dg}`, opciones {generar.OPCIONES}. Las 20 apps.",
         f"- Claude Code 2.1.312, `claude {flags}`, desde un directorio vacío de mktemp, sin herramientas. "
         f"Modelos informados: {sorted(modelos)}. Las 20 apps. Costo total informado: {costo:.2f} USD; segundos por Dockerfile (r0), media {sum(segs)/max(len(segs),1):.1f}.",
         "- hadolint 2.14.0 (`hadolint/hadolint:v2.14.0`), `-f json`, todos los niveles. Limpio = 0 avisos.",
         "- Construcción: `docker buildx build` con un builder propio (`v711-builder`, driver docker-container) y `--load`. Tamaño = DISK USAGE de "
         "`docker images` (descomprimida). Root = Config.User vacío, root o 0. latest = algún FROM sin etiqueta o con :latest.",
         "- Arranca = `docker run` (--cpus 1, --memory 1g) y curl desde otro contenedor a :8080/ responde «ok» antes de 40 s.",
         "- Bucle: si la ronda k tiene avisos y k<3, la misma IA recibe su Dockerfile, la salida de hadolint y los archivos del proyecto. "
         "Se construye y se ejecuta la ronda 0 y la última; las intermedias solo pasan por hadolint. Trampa = cada `# hadolint ignore` nuevo.",
         "- El banco se probó antes con 20 Dockerfiles de referencia escritos a mano (referencia/): ver abajo.", "",
         "### Prompt (ronda 0)", "", "```", generar.PROMPT, "```", "", "### Prompt (rondas 1-3)", "", "```", generar.PROMPT_ARREGLO, "```"]
    ref = []
    for f in sorted(glob.glob(os.path.join(AQUI, "referencia", "*.Dockerfile.medida.json"))):
        m = json.load(open(f, encoding="utf-8"))
        ref.append((m["app"], m))
    L.append("\n## Referencias escritas a mano (prueba del banco)\n")
    L.append(f"- Construyen {sum(m['construye'] for _, m in ref)}/20 · arrancan {sum(bool(m.get('arranca')) for _, m in ref)}/20 · "
             f"hadolint con avisos {sum(1 for _, m in ref if m['hadolint'])} · root {sum(1 for _, m in ref if m.get('root'))}")
    tabla_medidas(L, ref)
    for quien in ("qwen", "claude"):
        bloque(quien, res[quien], L)
    # fin de soporte de la versión del lenguaje en la imagen final (endoflife.date, consultado al generar)
    import datetime
    import re
    import urllib.request
    eol = {}
    for prod, pre in (("nodejs", "node"), ("python", "python")):
        with urllib.request.urlopen(f"https://endoflife.date/api/{prod}.json", timeout=30) as r:
            eol[pre] = {x["cycle"]: x["eol"] for x in json.load(r)}
    hoy = datetime.date.today().isoformat()
    L.append(f"\n## Versión del lenguaje fuera de soporte (endoflife.date/api, consultado {hoy})\n")
    for quien in ("qwen", "claude"):
        fuera = []
        for app, rs in res[quien].items():
            b = rs[0]["medida"]["bases"][-1]
            m = re.match(r"(node|python):(\d+(?:\.\d+)?)", b)
            if m:
                ciclo = m.group(2) if m.group(1) == "python" else m.group(2).split(".")[0]
                fin = eol[m.group(1)].get(ciclo)
                if fin and fin < hoy:
                    fuera.append(f"{app} ({b}, fin {fin})")
        L.append(f"- {quien}: {len(fuera)} → {fuera}")
    with open(os.path.join(AQUI, "SALIDA.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
