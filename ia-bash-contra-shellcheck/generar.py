# -*- coding: utf-8 -*-
"""Genera los scripts del 704 y corre el bucle «IA + ShellCheck» (rondas 0-3). Reanudable: no repite lo que ya está en muestras/.

  python generar.py qwen     # qwen2.5:7b por Ollama, las 50 tareas
  python generar.py claude   # Claude Code (claude -p), las 20 tareas impares 1-39
  python generar.py cruzado  # Claude Code arregla los scripts de qwen que tenían avisos en la ronda 0 (misma entrada que el bucle de qwen)

Ronda 0: el PROMPT de tareas.py. Ronda k+1 (si la ronda k tiene avisos y k < 3): PROMPT_ARREGLO con el script de la ronda k y la
salida de ShellCheck en formato gcc. Cada llamada es de un solo turno: la misma información para las dos IA.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

import banco
from tareas import CLAUDE_IDS, PROMPT, PROMPT_ARREGLO, T

AQUI = banco.AQUI
OLLAMA = "http://127.0.0.1:11434"
QWEN = "qwen2.5:7b"
OPCIONES = {"temperature": 0.2, "seed": 42, "num_ctx": 8192, "num_predict": 2048}
CLAUDE = r"C:\Users\tu-usuario\.vscode\extensions\anthropic.claude-code-2.1.312-win32-x64\resources\native-binary\claude.exe"
CLAUDE_FLAGS = ["-p", "--safe-mode", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--output-format", "json"]
MAX_RONDAS = 3


def extraer(texto):
    for pat in (r"```(?:bash|sh|shell)\s*\n(.*?)```", r"```[a-zA-Z]*\s*\n(.*?)```"):
        m = re.search(pat, texto, re.S)
        if m:
            return m.group(1).strip() + "\n"
    return texto.strip() + "\n"


def qwen(prompt):
    body = json.dumps({"model": QWEN, "stream": False, "options": OPCIONES,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    return d["message"]["content"], {"modelo": d.get("model"), "eval_count": d.get("eval_count")}


def claude(prompt):
    tmp = tempfile.mkdtemp(prefix="v704-")  # directorio vacío, fuera del repo
    t0 = time.time()
    r = subprocess.run([CLAUDE] + CLAUDE_FLAGS, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=tmp, timeout=600)
    d = json.loads(r.stdout)
    if d.get("is_error"):
        raise RuntimeError(d.get("result"))
    return d["result"], {"modelos": list(d.get("modelUsage", {}).keys()), "costo_usd": d.get("total_cost_usd"),
                         "segundos": round(time.time() - t0, 1), "tmp": tmp}


def main(quien):
    gen = {"qwen": qwen, "claude": claude, "cruzado": claude}[quien]
    ids = [t["id"] for t in T] if quien == "qwen" else CLAUDE_IDS
    if quien == "cruzado":  # la ronda 0 es la de qwen, copiada tal cual
        ids = []
        for t in T:
            src = os.path.join(AQUI, "muestras", "qwen", f"{t['id']:02d}")
            with open(os.path.join(src, "r0.sc.json"), encoding="utf-8") as f:
                if not json.load(f):
                    continue
            ids.append(t["id"])
            dst = os.path.join(AQUI, "muestras", "cruzado", f"{t['id']:02d}")
            os.makedirs(dst, exist_ok=True)
            for e in ("sh", "sc.json"):
                if not os.path.exists(os.path.join(dst, f"r0.{e}")):
                    with open(os.path.join(src, f"r0.{e}"), encoding="utf-8") as a:
                        txt = a.read()
                    with open(os.path.join(dst, f"r0.{e}"), "w", encoding="utf-8", newline="\n") as b:
                        b.write(txt)
    por_id = {t["id"]: t for t in T}
    for n in ids:
        d = os.path.join(AQUI, "muestras", quien, f"{n:02d}")
        os.makedirs(d, exist_ok=True)
        k = 0
        while True:
            sh, meta, scj = (os.path.join(d, f"r{k}.{e}") for e in ("sh", "json", "sc.json"))
            if not os.path.exists(sh):
                if k == 0:
                    prompt = PROMPT.format(**por_id[n])
                else:
                    with open(os.path.join(d, f"r{k-1}.sh"), encoding="utf-8") as f:
                        prev = f.read()
                    with open(os.path.join(d, f"r{k-1}.sc.json"), encoding="utf-8") as f:
                        prev_sc = json.load(f)
                    prompt = PROMPT_ARREGLO.format(script=prev.rstrip("\n"), avisos=banco.gcc(prev_sc))
                texto, info = gen(prompt)
                with open(sh, "w", encoding="utf-8", newline="\n") as f:
                    f.write(extraer(texto))
                with open(meta, "w", encoding="utf-8") as f:
                    json.dump({"prompt": prompt, "respuesta": texto, **info}, f, ensure_ascii=False, indent=1)
            if not os.path.exists(scj):
                with open(scj, "w", encoding="utf-8") as f:
                    json.dump(banco.shellcheck(sh), f, ensure_ascii=False)
            with open(scj, encoding="utf-8") as f:
                sc = json.load(f)
            print(quien, n, f"r{k}", len(sc), "avisos", flush=True)
            if not sc or k >= MAX_RONDAS:
                break
            k += 1


if __name__ == "__main__":
    main(sys.argv[1])
