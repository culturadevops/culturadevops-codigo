# -*- coding: utf-8 -*-
"""Genera los Dockerfiles del 711 y corre el bucle «IA + hadolint» (rondas 0-3). Reanudable.

  python generar.py qwen     # qwen2.5:7b por Ollama
  python generar.py claude   # Claude Code (claude -p, sin herramientas, desde un directorio vacío)

Las dos IA reciben las mismas 20 apps y los mismos prompts. Ronda k+1 si la ronda k tiene avisos de hadolint y k < 3.
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
from crear_apps import APPS

AQUI = banco.AQUI
OLLAMA = "http://127.0.0.1:11434"
QWEN = "qwen2.5:7b"
OPCIONES = {"temperature": 0.2, "seed": 42, "num_ctx": 8192, "num_predict": 2048}
CLAUDE = r"C:\Users\tu-usuario\.vscode\extensions\anthropic.claude-code-2.1.312-win32-x64\resources\native-binary\claude.exe"
CLAUDE_FLAGS = ["-p", "--safe-mode", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--output-format", "json"]
MAX_RONDAS = 3
LOCKS = ("package-lock.json", "go.sum")

PROMPT = """Escribe un Dockerfile de producción para esta aplicación. La aplicación tiene que escuchar en el puerto 8080.
El contexto de construcción es la carpeta del proyecto. Estos son sus archivos:

{archivos}

Responde solo con el Dockerfile completo dentro de un bloque ```dockerfile, sin explicaciones."""

PROMPT_ARREGLO = """Escribiste este Dockerfile para la aplicación de abajo:
```dockerfile
{dockerfile}
```
hadolint 2.14.0 da estos avisos:
{avisos}

Los archivos del proyecto (el contexto de construcción) son:

{archivos}

Corrige el Dockerfile para que hadolint no dé avisos. Responde solo con el Dockerfile completo dentro de un bloque ```dockerfile, sin explicaciones."""


def listado(app):
    raiz = os.path.join(AQUI, "apps", app)
    partes = []
    for d, _, fs in sorted(os.walk(raiz)):
        for f in sorted(fs):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, raiz).replace("\\", "/")
            with open(p, encoding="utf-8") as fh:
                txt = fh.read()
            if f in LOCKS:
                partes.append(f"--- {rel} --- (existe; no se muestra: {txt.count(chr(10))} líneas)")
            else:
                partes.append(f"--- {rel} ---\n{txt.rstrip()}")
    return "\n\n".join(partes)


def extraer(texto):
    for pat in (r"```(?:dockerfile|Dockerfile|docker)\s*\n(.*?)```", r"```[a-zA-Z]*\s*\n(.*?)```"):
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
    tmp = tempfile.mkdtemp(prefix="v711-")
    t0 = time.time()
    r = subprocess.run([CLAUDE] + CLAUDE_FLAGS, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=tmp, timeout=600)
    d = json.loads(r.stdout)
    if d.get("is_error"):
        raise RuntimeError(d.get("result"))
    return d["result"], {"modelos": list(d.get("modelUsage", {}).keys()), "costo_usd": d.get("total_cost_usd"),
                         "segundos": round(time.time() - t0, 1), "tmp": tmp}


def main(quien):
    gen = {"qwen": qwen, "claude": claude}[quien]
    for app in APPS:
        d = os.path.join(AQUI, "muestras", quien, app)
        os.makedirs(d, exist_ok=True)
        archivos = listado(app)
        k = 0
        while True:
            df, meta, hj = (os.path.join(d, f"r{k}.{e}") for e in ("Dockerfile", "json", "hadolint.json"))
            if not os.path.exists(df):
                if k == 0:
                    prompt = PROMPT.format(archivos=archivos)
                else:
                    with open(os.path.join(d, f"r{k-1}.Dockerfile"), encoding="utf-8") as f:
                        prev = f.read()
                    with open(os.path.join(d, f"r{k-1}.hadolint.json"), encoding="utf-8") as f:
                        prev_h = json.load(f)
                    prompt = PROMPT_ARREGLO.format(dockerfile=prev.rstrip("\n"), avisos=banco.tty(prev_h), archivos=archivos)
                texto, info = gen(prompt)
                with open(df, "w", encoding="utf-8", newline="\n") as f:
                    f.write(extraer(texto))
                with open(meta, "w", encoding="utf-8") as f:
                    json.dump({"prompt": prompt, "respuesta": texto, **info}, f, ensure_ascii=False, indent=1)
            if not os.path.exists(hj):
                with open(hj, "w", encoding="utf-8") as f:
                    json.dump(banco.hadolint(df), f, ensure_ascii=False)
            with open(hj, encoding="utf-8") as f:
                h = json.load(f)
            print(quien, app, f"r{k}", len(h), "avisos", flush=True)
            if not h or k >= MAX_RONDAS:
                break
            k += 1


if __name__ == "__main__":
    main(sys.argv[1])
