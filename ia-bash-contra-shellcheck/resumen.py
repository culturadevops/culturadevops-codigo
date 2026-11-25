# -*- coding: utf-8 -*-
"""Cuenta resultados.json y escribe SALIDA.md (todas las cifras del vídeo 704 salen de aquí)."""
import collections
import json
import os
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))


def estado(r):
    c, e = r["control"][1], r["espacios"][1]
    return "robusto" if c and e else ("rompe_espacios" if c else ("solo_espacios" if e else "no_funciona"))


def bloque(quien, por_id, L):
    n = len(por_id)
    r0 = [rs[0] for rs in por_id.values()]
    fin = [rs[-1] for rs in por_id.values()]
    con_av = [r for r in r0 if r["sc"]]
    cod = collections.Counter(a["code"] for r in r0 for a in r["sc"])
    archivos_cod = collections.Counter(c for r in r0 for c in {a["code"] for a in r["sc"]})
    nivel = collections.Counter(a["level"] for r in r0 for a in r["sc"])
    est0 = collections.Counter(estado(r) for r in r0)
    estf = collections.Counter(estado(r) for r in fin)
    fmt = collections.Counter(r["shfmt"] for r in r0)
    L.append(f"\n## {quien} — {n} scripts\n")
    L.append(f"- Ronda 0 con al menos un aviso de ShellCheck: **{len(con_av)} de {n}**; avisos en total: {sum(cod.values())}")
    L.append(f"- Por nivel: {dict(nivel)}")
    L.append("- Por código (avisos · scripts): " + ", ".join(f"SC{c} {v}·{archivos_cod[c]}" for c, v in cod.most_common()))
    L.append(f"- SC2086 (variable sin comillas): {cod.get(2086, 0)} avisos en {archivos_cod.get(2086, 0)} scripts")
    L.append(f"- shfmt -d en ronda 0: {dict(fmt)}  (ok = ya está en el formato de shfmt)")
    L.append(f"- Ejecución ronda 0: {dict(est0)}")
    L.append(f"- Líneas por script (ronda 0), media: {sum(r['lineas'] for r in r0) / n:.1f}")
    import re
    textos = [open(os.path.join(AQUI, r["ruta"]), encoding="utf-8").read() for r in r0]
    sin_com = ["\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#")) for t in textos]
    L.append(f"- Costumbres (ronda 0): set -euo pipefail en {sum('set -euo pipefail' in t for t in sin_com)}; "
             f"«--» como fin de opciones en {sum(bool(re.search(r'(^|[ ])--([ ]|$)', t, re.M)) for t in sin_com)}; "
             f"-print0 en {sum('-print0' in t for t in sin_com)}")
    L.append(f"- Limpios en ronda 0: {n - len(con_av)}; de ellos robustos al ejecutar: "
             f"{sum(1 for r in r0 if not r['sc'] and estado(r) == 'robusto')}")
    L.append(f"- Ejecución tras el bucle (última ronda): {dict(estf)}")
    limpio_y_rompe = [n_ for n_, rs in por_id.items() if not rs[0]["sc"] and estado(rs[0]) == "rompe_espacios"]
    limpio_no_func = [n_ for n_, rs in por_id.items() if not rs[0]["sc"] and estado(rs[0]) == "no_funciona"]
    L.append(f"- ShellCheck limpio en ronda 0 y aun así rompe con espacios: {len(limpio_y_rompe)} {limpio_y_rompe}")
    L.append(f"- ShellCheck limpio en ronda 0 y no hace la tarea ni sin espacios: {len(limpio_no_func)} {limpio_no_func}")
    # bucle
    if con_av:
        rondas_hasta = collections.Counter()
        supr_nuevas, reg, mejora = [], [], []
        for n_, rs in por_id.items():
            if not rs[0]["sc"]:
                continue
            k = next((r["k"] for r in rs if not r["sc"]), None)
            rondas_hasta["nunca (3 rondas)" if k is None else f"limpio en ronda {k}"] += 1
            s = rs[-1]["supr"] - rs[0]["supr"]
            if s > 0:
                supr_nuevas.append((n_, s))
            e0, ef = estado(rs[0]), estado(rs[-1])
            if e0 == "robusto" and ef != "robusto":
                reg.append((n_, e0, ef))
            if e0 != "robusto" and ef == "robusto":
                mejora.append((n_, e0, ef))
        L.append(f"- Bucle IA + ShellCheck sobre los {len(con_av)} con avisos: {dict(sorted(rondas_hasta.items()))}")
        L.append(f"- Supresiones nuevas (# shellcheck disable): {supr_nuevas or 'ninguna'}")
        L.append(f"- Funcionaban y el bucle los rompió: {reg or 'ninguno'}")
        orden = {"robusto": 2, "rompe_espacios": 1, "solo_espacios": 1, "no_funciona": 0}
        peor = [(n_, estado(rs[0]), estado(rs[-1])) for n_, rs in por_id.items() if rs[0]["sc"] and orden[estado(rs[-1])] < orden[estado(rs[0])]]
        L.append(f"- Empeoraron con el bucle (cualquier bajada): {peor or 'ninguno'}")
        L.append(f"- Limpios al final del bucle: {sum(1 for rs in por_id.values() if rs[0]['sc'] and not rs[-1]['sc'])}, "
                 f"de ellos robustos al ejecutar: {sum(1 for rs in por_id.values() if rs[0]['sc'] and not rs[-1]['sc'] and estado(rs[-1]) == 'robusto')}")
        L.append(f"- No funcionaban bien y el bucle los arregló: {mejora or 'ninguno'}")
    L.append("\n| tarea | avisos r0 | códigos r0 | rondas | avisos final | supr. | r0 control/espacios | final control/espacios | error con espacios (r0) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for n_, rs in sorted(por_id.items()):
        a, b = rs[0], rs[-1]
        cods = ",".join(sorted({str(x["code"]) for x in a["sc"]}))
        ok = lambda r: f"{'✔' if r['control'][1] else '✘'}/{'✔' if r['espacios'][1] else '✘'}"
        err = a["espacios"][2][:90].replace("|", "/") if not a["espacios"][1] else ""
        L.append(f"| {n_} | {len(a['sc'])} | {cods} | {len(rs)-1} | {len(b['sc'])} | {b['supr']-a['supr']} | {ok(a)} | {ok(b)} | {err} |")


def main():
    with open(os.path.join(AQUI, "resultados.json"), encoding="utf-8") as f:
        res = {q: {int(k): v for k, v in d.items()} for q, d in json.load(f).items()}
    digest = json.loads(subprocess.run(["curl", "-s", "http://127.0.0.1:11434/api/tags"], capture_output=True, text=True).stdout)
    dg = next((m["digest"] for m in digest["models"] if m["name"] == "qwen2.5:7b"), "?")
    cl = json.load(open(os.path.join(AQUI, "muestras", "claude", "01", "r0.json"), encoding="utf-8"))
    costos, segs = {}, []
    for carpeta in ("claude", "cruzado"):
        for d, _, fs in os.walk(os.path.join(AQUI, "muestras", carpeta)):
            for f_ in fs:
                if f_.endswith(".json") and not f_.endswith("sc.json"):
                    j = json.load(open(os.path.join(d, f_), encoding="utf-8"))
                    costos[carpeta] = costos.get(carpeta, 0) + (j.get("costo_usd") or 0)
                    if carpeta == "claude" and f_ == "r0.json":
                        segs.append(j.get("segundos") or 0)
    costo = sum(costos.values())
    costo = f"{costo:.2f} (generar 20: {costos.get('claude', 0):.2f}; arreglar 13: {costos.get('cruzado', 0):.2f}); " \
            f"segundos por script en ronda 0, media: {sum(segs) / max(len(segs), 1):.1f}"
    L = ["# SALIDA — 704 · 50 scripts de Bash escritos por IA contra ShellCheck",
         "", "Generado por `resumen.py` a partir de `resultados.json` (`generar.py` → `analizar.py` → `resumen.py`; `ejecutar_todo.py` lo corre todo).",
         "Fecha de la medición: 2026-10-29. **No es un estudio**: 50 tareas fijas, un modelo local y una muestra de 20 con Claude Code.", "",
         "## Montaje", "",
         f"- Modelo local: `qwen2.5:7b` por Ollama, digest `{dg}`, /api/chat, opciones temperature=0.2, seed=42, num_ctx=8192, num_predict=2048.",
         f"- Claude Code 2.1.312 (`claude -p --safe-mode --tools \"\" --strict-mcp-config --no-session-persistence --output-format json`), "
         f"desde un directorio vacío de mktemp, sin herramientas. Modelos que informó: {cl['modelos']}. Costo total informado (USD): {costo}.",
         "  (`--bare` existe, pero exige ANTHROPIC_API_KEY y la cuenta del dueño es OAuth: `--safe-mode` desactiva CLAUDE.md, hooks, skills y MCP.)",
         "- Muestra de Claude Code: las 20 tareas impares del 1 al 39 (fijada antes de generar).",
         "- ShellCheck 0.11.0 (`koalaman/shellcheck:v0.11.0`, sha256:61862eba…), `-f json1`, todos los niveles. shfmt v3.12.0 (`mvdan/shfmt:v3.12.0`), `-d`.",
         "- Ejecución: contenedor desechable `--rm --network none` (debian:bookworm-20251020-slim + procps, bash 5.2.15). Cada script corre dos veces, "
         "cada una en su propio mktemp: **control** (nombres con `_`) y **espacios** (los mismos nombres con espacios). Un check en bash por tarea "
         "(tareas.py) dice si la tarea quedó hecha. Timeout 20 s.",
         "- El banco se probó antes con 50 soluciones de referencia escritas a mano (`referencia.py`): 50/50 pasan control y espacios; "
         "y con dos scripts sin comillas (fallan solo con espacios, como debe ser).",
         "- Bucle: si la ronda k tiene avisos y k<3, se le da a la misma IA su script y la salida de ShellCheck (formato gcc) y se le pide corregirlo. "
         "Un solo turno por llamada. Cuenta como trampa cada `# shellcheck disable` nuevo frente a la ronda 0.",
         "- Criterios fijados antes de mirar: funciona = check OK en control; rompe con espacios = OK en control y falla con espacios; limpio = 0 avisos.",
         "", "### Prompt (ronda 0)", "", "```", __import__("tareas").PROMPT, "```", "", "### Prompt (rondas 1-3)", "", "```",
         __import__("tareas").PROMPT_ARREGLO, "```"]
    for quien in ("qwen", "claude"):
        bloque(quien, res[quien], L)
    # mismo estado: las 20 tareas que hicieron las dos
    L.append("\n## Comparación en las MISMAS 20 tareas (impares 1-39)\n")
    for quien in ("qwen", "claude"):
        sub = {n: res[quien][n] for n in range(1, 40, 2)}
        r0 = [rs[0] for rs in sub.values()]
        L.append(f"- {quien}: ronda 0 con avisos {sum(1 for r in r0 if r['sc'])}/20 · avisos {sum(len(r['sc']) for r in r0)} · "
                 f"ejecución r0 {dict(collections.Counter(estado(r) for r in r0))}")
    # bucle cruzado: los mismos 13 scripts de qwen con avisos, arreglados por qwen y por Claude Code
    L.append("\n## Bucle cruzado: los MISMOS scripts de qwen con avisos, arreglados por cada IA\n")
    L.append("`python generar.py cruzado`: la ronda 0 es la de qwen copiada tal cual; las rondas 1-3 las hace Claude Code con el mismo PROMPT_ARREGLO.")
    bloque("cruzado (arregla Claude Code)", res["cruzado"], L)
    with open(os.path.join(AQUI, "SALIDA.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[30:]))


if __name__ == "__main__":
    main()
