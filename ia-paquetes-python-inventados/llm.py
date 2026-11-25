# -*- coding: utf-8 -*-
"""Llamadas a las dos IA, iguales para los vídeos 706 y 707.

- qwen: Ollama local, /api/chat, temperature y seed fijos.
- claude: Claude Code 2.1.312 en modo -p, desde un directorio temporal vacío, con --safe-mode (sin CLAUDE.md,
  hooks, MCP ni skills), --tools "" (ninguna herramienta: no puede leer ni escribir nada) y sin variables de
  credenciales en el entorno. --bare no sirve aquí: exige ANTHROPIC_API_KEY y la cuenta es OAuth.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

OLLAMA = "http://127.0.0.1:11434"
QWEN = "qwen2.5:7b"
CLAUDE = r"C:\Users\tu-usuario\.vscode\extensions\anthropic.claude-code-2.1.312-win32-x64\resources\native-binary\claude.exe"
PARAMS = {"temperature": 0.7, "top_p": 0.9, "num_ctx": 8192}


def qwen_digest():
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as r:
        for m in json.load(r)["models"]:
            if m["name"] == QWEN:
                return m["digest"]
    return "?"


def qwen(prompt, seed):
    body = {"model": QWEN, "stream": False, "messages": [{"role": "user", "content": prompt}],
            "options": dict(PARAMS, seed=seed)}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        d = json.load(r)
    return {"texto": d["message"]["content"], "modelo": QWEN, "seed": seed, "s": round(time.time() - t, 1),
            "tokens": d.get("eval_count")}


def _env_limpio():
    env = {k: v for k, v in os.environ.items()
           if not re.match(r"^(AWS|KUBE|GITHUB|GH_|AZURE|GOOGLE|ANTHROPIC_API|DOCKER_HOST)", k, re.I)}
    env.update({"AWS_SHARED_CREDENTIALS_FILE": "/nonexistent", "AWS_CONFIG_FILE": "/nonexistent", "KUBECONFIG": "/nonexistent"})
    return env


def claude(prompt):
    tmp = tempfile.mkdtemp(prefix="v7xx-claude-")
    t = time.time()
    try:
        p = subprocess.run([CLAUDE, "-p", "--safe-mode", "--tools", "", "--output-format", "json",
                            "--no-session-persistence", "--max-budget-usd", "1"],
                           input=prompt, capture_output=True, text=True, encoding="utf-8", cwd=tmp, env=_env_limpio(), timeout=900)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    d = json.loads(p.stdout)
    modelos = [m for m in d.get("modelUsage", {}) if "haiku" not in m] or list(d.get("modelUsage", {}))
    return {"texto": d.get("result", ""), "modelo": ",".join(modelos), "s": round(time.time() - t, 1),
            "usd": d.get("total_cost_usd"), "error": d.get("is_error")}


def bloques(texto, langs=("hcl", "terraform", "tf", "")):
    """Todos los bloques de código ``` de esos lenguajes, unidos."""
    out = []
    for m in re.finditer(r"```([a-zA-Z0-9_+-]*)[^\n]*\n(.*?)```", texto, re.S):
        if m.group(1).lower() in langs:
            out.append(m.group(2))
    return "\n".join(out)
