# -*- coding: utf-8 -*-
"""707 · Regenera SALIDA.md. NUNCA instala un paquete inventado.

  python ejecutar_todo.py              # vuelve a consultar PyPI (borra la caché), repite la demo de defensas y escribe SALIDA.md
  python ejecutar_todo.py --con-cache  # usa la caché de PyPI de medidas/pypi_cache.json
  python ejecutar_todo.py --generar    # además genera lo que falte (Ollama y la cuenta de Claude)
"""
import collections
import datetime
import json
import pathlib
import subprocess
import sys

from llm import PARAMS, QWEN, qwen_digest
from peticiones import PETICIONES, PLANTILLA

AQUI = pathlib.Path(__file__).parent
PY = sys.executable
REPE = ["c10", "c13", "c22", "n01", "n03", "n10", "n11", "n13", "n20", "n28", "n36", "n45"]
ESTANDAR = {"subprocess", "json"}
TAREA = dict(PETICIONES)


def stats(filas):
    pips = [p for f in filas for p in f["pip"]]
    bad = [(f["id"], p[0]) for f in filas for p in f["pip"] if p[1] is False]
    return {"resp": len(filas), "con_pip": sum(bool(f["pip"]) for f in filas), "pips": len(pips),
            "unicos": len({p[0].lower() for p in pips}), "bad": bad, "bad_unicos": len({b[1].lower() for b in bad}),
            "resp_bad": len({b[0] for b in bad}), "pct": round(100 * len(bad) / len(pips), 1) if pips else 0}


def main():
    if "--generar" in sys.argv:
        subprocess.run([PY, "generar.py", "qwen", "1"], check=True, cwd=AQUI)
        subprocess.run([PY, "generar.py", "claude"], check=True, cwd=AQUI)
        subprocess.run([PY, "generar.py", "qwen", *map(str, range(2, 11)), "--solo", *REPE], check=True, cwd=AQUI)
    if "--con-cache" not in sys.argv:
        (AQUI / "medidas" / "pypi_cache.json").unlink(missing_ok=True)
    subprocess.run([PY, "analizar.py"], check=True, cwd=AQUI)
    subprocess.run([PY, "demo_defensas.py"], check=True, cwd=AQUI, capture_output=True)
    A = json.loads((AQUI / "medidas" / "analisis.json").read_text(encoding="utf-8"))
    cache = json.loads((AQUI / "medidas" / "pypi_cache.json").read_text(encoding="utf-8"))
    L = []
    w = L.append
    w("# SALIDA · 707 · La IA se inventa paquetes de Python")
    w(f"\nGenerado por `ejecutar_todo.py` el {datetime.date.today().isoformat()}. Existencia comprobada con GET a "
      "`https://pypi.org/pypi/<nombre>/json` (200 = existe, 404 = no existe) ese mismo día. Nada se instaló.")
    w("\n## Modelos y parámetros\n")
    w(f"- `{QWEN}` digest `{qwen_digest()}`, Ollama `/api/chat`, opciones {json.dumps(PARAMS)}, seed 1 (100 prompts) y "
      "seeds 2-10 para las repeticiones.")
    cl = json.loads(next((AQUI / "respuestas" / "claude").glob("*.json")).read_text(encoding="utf-8"))
    usd = sum(json.loads(f.read_text(encoding="utf-8")).get("usd") or 0 for f in (AQUI / "respuestas" / "claude").glob("*.json"))
    w(f"- Claude Code 2.1.312, `claude -p --safe-mode --tools \"\" --output-format json --no-session-persistence`, desde un "
      f"directorio temporal vacío y sin credenciales. Modelo: `{cl['modelo']}`. Muestra: 1 de cada 4 prompts (25), fijada antes de "
      f"generar. Coste informado por Claude Code: {usd:.2f} USD. La temperatura no se puede fijar.")
    w(f"- Biblioteca estándar: `sys.stdlib_module_names` de Python {sys.version.split()[0]}.")
    w("\n## Prompt (igual para las dos IA)\n\n```\n" + PLANTILLA + "\n```\n")
    w("100 tareas: c01-c50 comunes (Excel, API REST, S3, Slack…) y n01-n50 de nicho DevOps (terraform plan, HCL, OPA, Vault…). "
      "Lista completa en peticiones.py.")
    w("\n## Criterio (fijado antes de generar)\n")
    w("- Inventado = un nombre de `pip install` que da 404 en PyPI. Se cuentan todas las apariciones (una por respuesta).")
    w("- Los imports se traducen a su paquete con la tabla IMPORT_A_PAQUETE de peticiones.py (`import yaml` → `pyyaml`). "
      "Añadido después de ver las respuestas: `markdown_it` → `markdown-it-py` (caso documentado). Los stubs generados de gRPC "
      "(`*_pb2`) y los módulos de ejemplo `your_*` se cuentan como locales.")
    w("- Muestra: 100 respuestas de qwen y 25 de Claude. No es un estudio.")

    w("\n## Resultado: nombres de pip install que no existen en PyPI\n")
    w("| IA | respuestas | con pip install | nombres (apariciones) | únicos | NO existen | % apariciones | respuestas con ≥1 inventado |")
    w("|---|---|---|---|---|---|---|---|")
    filas = {"qwen-s1": A["qwen-s1"], "claude": A["claude"]}
    for l, fs in filas.items():
        s = stats(fs)
        w(f"| {l} | {s['resp']} | {s['con_pip']} | {s['pips']} | {s['unicos']} | {len(s['bad'])} ({s['bad_unicos']} únicos) | {s['pct']} % | {s['resp_bad']} |")
    for grupo, pre in [("comunes", "c"), ("nicho", "n")]:
        s = stats([f for f in A["qwen-s1"] if f["id"].startswith(pre)])
        w(f"| qwen-s1 · {grupo} | {s['resp']} | {s['con_pip']} | {s['pips']} | {s['unicos']} | {len(s['bad'])} | {s['pct']} % | {s['resp_bad']} |")
    w("\n### Los nombres que no existen (qwen-s1)\n")
    w("| prompt | tarea | pip install … | tipo |")
    w("|---|---|---|---|")
    for pid, n in stats(A["qwen-s1"])["bad"]:
        tipo = "módulo de la biblioteca estándar" if n in ESTANDAR else ("palabra del prompt" if n == "necesario" else "nombre inventado")
        w(f"| {pid} | {TAREA[pid]} | `{n}` | {tipo} |")
    w("\nComprobación (GET a la API de PyPI): " + "; ".join(
        f"`{n}` → {'404' if not cache.get(n.lower().replace('_', '-'), {}).get('existe') else '200'}"
        for _, n in stats(A["qwen-s1"])["bad"]))

    w("\n## Imports: el nombre del import no es el del paquete\n")
    for l, fs in filas.items():
        imps = [i for f in fs for i in f["imports"]]
        dist = sorted({(i["import"], i["paquete"], i["literal_existe"]) for i in imps if i["distinto"]})
        w(f"- {l}: {len(imps)} imports de terceros; {sum(i['distinto'] for i in imps)} con nombre distinto al paquete. Pares "
          "(import → paquete; ¿existe en PyPI un paquete con el nombre del import?): " +
          "; ".join(f"`{a}` → `{b}` ({'sí' if c else 'no'})" for a, b, c in dist))
        sinpip = [(f["id"], i["import"], i["paquete"], i["existe"]) for f in fs for i in f["imports"] if not i["en_pip"]]
        w(f"  - Imports sin su paquete en el pip install: " + "; ".join(f"{a} `{b}` (→ `{c}`, {'existe' if d else 'NO existe'})" for a, b, c, d in sinpip))
    w("\n### Nombres que existen en PyPI pero son otra cosa (solo metadatos, nada instalado)\n")
    for n in ["journal", "config", "dockerfile", "terraform", "yaml", "hcl2", "python-hcl2", "dockerfile-py", "dockerfile-parse"]:
        c = cache.get(n) or {}
        if not c:
            continue
        w(f"- `{n}`: " + (f"existe · «{c.get('resumen')}» · {c.get('versiones')} versiones · primera subida {c.get('primera')} · última {c.get('ultima')}"
                          if c.get("existe") else "404, no existe"))

    w("\n## Repetición: los 12 prompts con un nombre inventado, 10 veces (seeds 1-10)\n")
    w("| prompt | nombre inventado (seed 1) | aparece en N de 10 | otros nombres inexistentes en las repeticiones |")
    w("|---|---|---|---|")
    rep_total = collections.Counter()
    for pid in REPE:
        nombres_s1 = [n for p, n in stats(A["qwen-s1"])["bad"] if p == pid]
        apar = collections.Counter()
        otros = set()
        for seed in range(1, 11):
            f = [x for x in A.get(f"qwen-s{seed}", []) if x["id"] == pid]
            if not f:
                continue
            malos = {p[0].lower() for p in f[0]["pip"] if p[1] is False}
            for n in nombres_s1:
                if n.lower() in malos:
                    apar[n] += 1
            otros |= malos - {n.lower() for n in nombres_s1}
        for n in nombres_s1:
            rep_total[apar[n]] += 1
            w(f"| {pid} | `{n}` | {apar[n]} | {', '.join(sorted(otros)) or '—'} |")
    w(f"\nDistribución (cuántos nombres aparecen en N de 10): {dict(sorted(rep_total.items()))}")

    w("\n## pip-audit y las defensas (salida literal de demo_defensas.py, en python:3.12.16-bookworm con --rm)\n")
    w("```\n" + (AQUI / "medidas" / "demo_defensas.txt").read_text(encoding="utf-8").strip() + "\n```")
    w("\n## Fuente de comparación\n")
    w("Spracklen et al., «We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs», "
      "34th USENIX Security Symposium, ago-2025, pp. 3687-3706 (https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen; "
      "texto en arXiv 2406.10279v3, mar-2025):19,7 % de 2,23 millones de paquetes recomendados no existían; Python "
      "15,8 %, JavaScript 21,3 %; modelos comerciales ~5,2 %, abiertos 21,7 %; 205.474 nombres inventados únicos; 43 % reaparecen "
      "en las 10 repeticiones y 58 % más de una vez. Listas maestras de PyPI y npm del 10-ene-2024.")
    (AQUI / "SALIDA.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("SALIDA.md escrito")


if __name__ == "__main__":
    main()
