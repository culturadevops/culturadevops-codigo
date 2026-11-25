# -*- coding: utf-8 -*-
"""Vídeo 708 · «AGENTS.md pide, el hook obliga». Regenera SALIDA.md.

Experimento (fijado ANTES de mirar resultados):
  · 10 tareas (4 Go, 3 Python, 3 Bash: ver TAREAS) sobre la misma semilla: un proyecto pequeño en Go, Python y Bash
    cuyos tres archivos ya traen deuda de linter (calc.go sin gofmt, inventario.py con import sin usar,
    respaldo.sh con variables sin comillas).
  · Condición A: AGENTS.md con la regla «pasa gofmt/go vet, ruff, shellcheck antes de terminar». Sin hook.
  · Condición B: el MISMO AGENTS.md + hook PostToolUse (matcher Edit|Write) que corre el verificador y sale con 2.
    Es la única variable que cambia.
  · Éxito de una corrida = todos los archivos de código que la corrida cambió o creó pasan su verificador
    (Go: gofmt -l vacío + go vet ./...; Python: ruff check; Bash: shellcheck). Se cuentan también: si Claude
    ejecutó el verificador por su cuenta, cuántas veces bloqueó el hook, supresiones nuevas y si la tarea se hizo.
  · Cada corrida: directorio temporal nuevo (tempfile.mkdtemp), copia limpia de la semilla, su propio
    .claude/settings.json de proyecto. Claude Code con --setting-sources project (no lee ~/.claude/settings.json)
    y sin variables CLAUDE_* ni credenciales en el entorno. Nunca bypassPermissions.

Uso:
  python ejecutar_todo.py            # corre lo que falte (reanudable: resultados.json) y escribe SALIDA.md
  python ejecutar_todo.py --informe  # solo reescribe SALIDA.md con lo ya medido
  python ejecutar_todo.py --piloto   # una corrida de prueba (T05, B) que NO entra en la cuenta
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SEMILLA = AQUI / "semilla"
HOOK = AQUI / "hook" / "verificar.py"
CORRIDAS = AQUI / "corridas"
RESULTADOS = AQUI / "resultados.json"
CLAUDE = Path(r"C:\Users\tu-usuario\.vscode\extensions\anthropic.claude-code-2.1.312-win32-x64\resources\native-binary\claude.exe")
VENV = Path(tempfile.gettempdir()) / "v708-venv"
VERSIONES = {"ruff": "0.17.3", "shellcheck-py": "0.11.0.1"}
MODELO = "sonnet"

TAREAS = [
    ("T01", "go", "En go/calc.go agrega una función exportada Mediana(xs []float64) (float64, bool) que devuelva la mediana; ok es false si el slice está vacío. No cambies lo que hacen las funciones que ya existen.", "func Mediana"),
    ("T02", "go", "En go/calc.go agrega Promedio(xs []float64) (float64, error), que devuelva un error si el slice está vacío.", "func Promedio"),
    ("T03", "go", "En go/calc.go agrega Acotar(v, lo, hi int) int, que devuelva v limitado al rango [lo, hi].", "func Acotar"),
    ("T04", "go", "Crea go/texto.go con una función exportada Invertir(s string) string que invierta la cadena por runas, no por bytes.", "func Invertir"),
    ("T05", "py", "En py/inventario.py agrega valor_total(items) que devuelva la suma de cantidad por precio de todos los artículos.", "def valor_total"),
    ("T06", "py", "En py/inventario.py agrega buscar(items, nombre) que devuelva el Articulo con ese nombre, o None si no está.", "def buscar"),
    ("T07", "py", "En py/inventario.py agrega desde_csv(texto: str) -> list[Articulo], que lea un CSV con columnas nombre,cantidad,precio usando el módulo csv.", "def desde_csv"),
    ("T08", "sh", "En sh/respaldo.sh agrega una opción -z que, en lugar de copiar, comprima el respaldo en un .tar.gz. No ejecutes el script.", "tar"),
    ("T09", "sh", "En sh/respaldo.sh haz que el script termine con un mensaje claro si ORIGEN no existe o no es un directorio. No ejecutes el script.", "-d"),
    ("T10", "sh", "En sh/respaldo.sh agrega, al terminar, una línea con fecha y hora en DESTINO/respaldos.log. No ejecutes el script.", "respaldos.log"),
]
CIERRE = " Al terminar, responde en una línea qué cambiaste."
# Segunda tanda (decidida tras ver A=B=10/10, antes de correrla): el mismo AGENTS.md, pero alguien agregó un CLAUDE.md
# corto (lo típico tras /init o de otro compañero) que no repite la regla. C = sin hook, D = con hook.
TAREAS_CD = ("T01", "T05", "T06", "T09")
CLAUDE_MD = "# Notas para Claude\n\n- Responde en español.\n- Comentarios del código en español.\n"
CONDICIONES = {"A": "A · solo AGENTS.md", "B": "B · AGENTS.md + hook PostToolUse",
               "C": "C · AGENTS.md + un CLAUDE.md corto (sin la regla), sin hook",
               "D": "D · AGENTS.md + CLAUDE.md corto + hook PostToolUse"}

PERMISOS = {"allow": [f"{t}({c} *)" for t in ("Bash", "PowerShell")
                      for c in ("gofmt", "go vet", "go build", "go test", "ruff", "shellcheck", "bash -n")]}
HOOKS_B = {"PostToolUse": [{"matcher": "Edit|Write", "hooks": [
    {"type": "command", "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/verificar.py"', "timeout": 60}]}]}
VERIF_RE = re.compile(r"\b(gofmt|go vet|ruff|shellcheck)\b")
SUPRESION_RE = re.compile(r"noqa|shellcheck\s+disable|nolint|type:\s*ignore")
EXT = {".go": "go", ".py": "py", ".sh": "sh"}
resultados_extra = {}


def asegurar_venv():
    exe = VENV / "Scripts" / "ruff.exe"
    if not exe.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        subprocess.run([str(VENV / "Scripts" / "pip"), "install", "-q"] + [f"{k}=={v}" for k, v in VERSIONES.items()], check=True)
    return VENV / "Scripts"


def entorno(scripts):
    env = {k: v for k, v in os.environ.items()
           if not re.match(r"(CLAUDE|ANTHROPIC|AWS_|KUBECONFIG|GITHUB_TOKEN|GH_TOKEN|AZURE_|GOOGLE_)", k)}
    env["PATH"] = str(scripts) + os.pathsep + env["PATH"]
    return env


def correr(cmd, cwd, env):
    cmd = [shutil.which(cmd[0], path=env["PATH"]) or cmd[0]] + list(cmd[1:])
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def verificar(ruta: Path, proyecto: Path, env):
    lang = EXT[ruta.suffix]
    if lang == "go":
        _, s = correr(["gofmt", "-l", str(ruta)], proyecto, env)
        rc, v = correr(["go", "vet", "./..."], proyecto / "go", env)
        return (not s and rc == 0), (s + "\n" + v).strip()
    if lang == "py":
        rc, s = correr(["ruff", "check", "--no-cache", str(ruta)], proyecto, env)
        return rc == 0, s
    rc, s = correr(["shellcheck", str(ruta)], proyecto, env)
    return rc == 0, s


def compila(ruta: Path, proyecto: Path, env):
    lang = EXT[ruta.suffix]
    if lang == "go":
        return correr(["go", "build", "./..."], proyecto / "go", env)[0] == 0
    if lang == "py":
        return correr([sys.executable, "-m", "py_compile", str(ruta)], proyecto, env)[0] == 0
    return correr(["bash", "-n", ruta.relative_to(proyecto).as_posix()], proyecto, env)[0] == 0


def archivos_codigo(raiz: Path):
    return {p.relative_to(raiz).as_posix(): p.read_bytes() for p in raiz.rglob("*")
            if p.is_file() and p.suffix in EXT and ".claude" not in p.parts}


def preparar(cond):
    d = Path(tempfile.mkdtemp(prefix="v708-"))
    shutil.copytree(SEMILLA, d, dirs_exist_ok=True)
    # Las reglas allow de un .claude/settings.json de proyecto NO se aplican en `claude -p` sin confianza en la carpeta
    # (permissions.md, «What runs before you trust a folder»; el log de depuración dice «Dropped 14 project-scoped
    # permissions.allow entries — workspace not yet trusted»). Por eso los permisos van por --allowedTools, igual en A y B,
    # y el settings.json del proyecto solo lleva el hook (los hooks SÍ se usan en -p).
    cfg = {}
    if cond in ("C", "D"):
        # memory.md: con un CLAUDE.md en el directorio, Claude Code lee «Your CLAUDE.md files only», no el AGENTS.md.
        (d / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")
    if cond in ("B", "D"):
        (d / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(HOOK, d / ".claude" / "hooks" / "verificar.py")
        cfg["hooks"] = HOOKS_B
    (d / ".claude").mkdir(exist_ok=True)
    (d / ".claude" / "settings.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return d


def lanzar(d: Path, prompt, env, jsonl: Path):
    cmd = [str(CLAUDE), "-p", prompt, "--model", MODELO, "--setting-sources", "project", "--no-session-persistence",
           "--output-format", "stream-json", "--verbose", "--include-hook-events", "--permission-mode", "acceptEdits",
           "--permission-prompts", "none", "--max-budget-usd", "1.5", "--allowedTools", *PERMISOS["allow"]]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=d, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    jsonl.write_text(r.stdout, encoding="utf-8")
    return time.time() - t0, r.stdout


def analizar_stream(texto):
    llamadas, verif, modelo, costo, turnos, final, avisos_hook = [], 0, None, None, None, "", 0
    for linea in texto.splitlines():
        try:
            m = json.loads(linea)
        except ValueError:
            continue
        if m.get("type") == "system" and m.get("subtype") == "init":
            modelo = m.get("model")
        if m.get("type") == "assistant":
            for b in m["message"].get("content", []):
                if b.get("type") == "tool_use":
                    cmd = b["input"].get("command", "") if b["name"] in ("Bash", "PowerShell") else ""
                    fp = Path(b["input"].get("file_path", "") or "").name
                    llamadas.append(b["name"] + (": " + cmd[:120] if cmd else (f"({fp})" if fp else "")))
                    if cmd and VERIF_RE.search(cmd):
                        verif += 1
        if m.get("type") == "user":
            for b in m["message"].get("content", []) if isinstance(m["message"].get("content"), list) else []:
                if b.get("type") == "tool_result" and "no pasa el verificador" in json.dumps(b, ensure_ascii=False):
                    avisos_hook += 1
        if m.get("type") == "result":
            costo, turnos, final = m.get("total_cost_usd"), m.get("num_turns"), m.get("result", "")
            if m.get("modelUsage"):
                modelo = ", ".join(m["modelUsage"].keys())
    return dict(llamadas=llamadas, verif_por_claude=verif, modelo=modelo, costo=costo, turnos=turnos,
                final=final, avisos_hook_en_stream=avisos_hook)


def medir(tid, lang, prompt, esperado, cond, env, nombre=None):
    d = preparar(cond)
    antes = archivos_codigo(d)
    CORRIDAS.mkdir(exist_ok=True)
    seg, stream = lanzar(d, prompt + CIERRE, env, CORRIDAS / f"{nombre or tid + '-' + cond}.jsonl")
    despues = archivos_codigo(d)
    tocados = sorted(k for k, v in despues.items() if antes.get(k) != v)
    res = {"tarea": tid, "lang": lang, "cond": cond, "segundos": round(seg), "tocados": tocados, "archivos": {}}
    for k in tocados:
        ok, salida = verificar(d / k, d, env)
        res["archivos"][k] = {"pasa": ok, "compila": compila(d / k, d, env), "salida": salida[:600]}
    texto = "".join(despues[k].decode("utf-8", "replace") for k in tocados)
    res["tarea_hecha"] = esperado in texto
    res["supresiones_nuevas"] = len(SUPRESION_RE.findall(texto)) - sum(
        len(SUPRESION_RE.findall(antes[k].decode("utf-8", "replace"))) for k in tocados if k in antes)
    res["exito"] = bool(tocados) and all(a["pasa"] for a in res["archivos"].values())
    reg = d / ".claude" / "hooks" / "registro.log"
    lineas = reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []
    res["hook_disparos"] = len(lineas)
    res["hook_bloqueos"] = sum(1 for x in lineas if '"bloquea": true' in x)
    no_tocados = {k for k in antes if k not in tocados}
    res["deuda_en_no_tocados"] = sorted(k for k in no_tocados if not verificar(d / k, d, env)[0])
    res.update(analizar_stream(stream))
    res["dir"] = str(d)
    shutil.rmtree(d, ignore_errors=True)
    return res


def hook_aislado(env):
    """El hook sin Claude: JSON por stdin sobre la semilla. Lo que se ve en pantalla."""
    d = preparar("B")
    filas = []
    for k in ("go/calc.go", "py/inventario.py", "sh/respaldo.sh"):
        entrada = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(d / k)}})
        e2 = dict(env, CLAUDE_PROJECT_DIR=str(d))
        r = subprocess.run([sys.executable, str(d / ".claude/hooks/verificar.py")], input=entrada, cwd=d, env=e2,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        filas.append((k, r.returncode, r.stderr.strip().replace(str(d) + os.sep, "")))
    shutil.rmtree(d, ignore_errors=True)
    return filas


def semilla(env):
    """La deuda de partida, tal cual la ven los linters (sin Claude)."""
    d = preparar("A")
    filas = [(" ".join(c), correr(c, d, env)[1]) for c in (["gofmt", "-l", "go/"], ["ruff", "check", "--no-cache", "py/inventario.py"],
                                                          ["shellcheck", "sh/respaldo.sh"])]
    shutil.rmtree(d, ignore_errors=True)
    return filas


def prueba_confianza(env):
    """¿Se aplican en -p las reglas allow del .claude/settings.json del proyecto? Una corrida sin herramientas con --debug-file."""
    d = Path(tempfile.mkdtemp(prefix="v708-confianza-"))
    (d / ".claude").mkdir()
    (d / ".claude" / "settings.json").write_text(json.dumps({"permissions": PERMISOS}, indent=2), encoding="utf-8")
    dbg = d / "debug.log"
    r = subprocess.run([str(CLAUDE), "-p", "Responde solo: ok", "--model", MODELO, "--setting-sources", "project",
                        "--no-session-persistence", "--tools", "", "--debug-file", str(dbg)], cwd=d, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    lineas = [x[x.find("[DEBUG]"):] for x in dbg.read_text(encoding="utf-8", errors="replace").splitlines()
              if re.search(r"trusted|Dropped \d+ project", x)]
    shutil.rmtree(d, ignore_errors=True)
    return {"debug": lineas, "stderr": r.stderr.strip()[:500], "stdout": r.stdout.strip()[:200]}


def informe(resultados, aislado, env):
    _, gover = correr(["go", "version"], AQUI, env)
    _, rv = correr(["ruff", "--version"], AQUI, env)
    _, sv = correr(["shellcheck", "--version"], AQUI, env)
    _, cv = correr([str(CLAUDE), "--version"], AQUI, env)
    sv = next((x for x in sv.splitlines() if x.startswith("version")), sv)
    L = ["# SALIDA · 708 «AGENTS.md pide, el hook obliga»", "",
         f"Generado por `ejecutar_todo.py` el {time.strftime('%Y-%m-%d %H:%M')}. No editar a mano.", "",
         "## Versiones", "", f"- Claude Code: `{cv}` (`{CLAUDE.name}` de la extensión de VS Code)",
         f"- Modelo pedido: `--model {MODELO}`; modelos que respondieron: "
         f"`{sorted({r['modelo'] for r in resultados.values() if r.get('modelo')})}`",
         f"- {gover} · {rv} · shellcheck {sv}", "",
         "## Flags de cada corrida", "",
         "`claude -p <tarea> --model sonnet --setting-sources project --no-session-persistence --output-format stream-json "
         "--verbose --include-hook-events --permission-mode acceptEdits --permission-prompts none --max-budget-usd 1.5 --allowedTools <lista>`", "",
         f"`--allowedTools`: {' '.join(PERMISOS['allow'])}", "",
         "Las reglas allow de `.claude/settings.json` de proyecto no se aplican en `-p` (carpeta sin confianza): el log de "
         "depuración dice `Dropped 14 project-scoped permissions.allow entries — workspace not yet trusted` (piloto 0). Los hooks del "
         "mismo archivo sí corren. Por eso los permisos van por flag, iguales en A y B.", "",
         "Sin `--bare`: `--bare` se salta los hooks (lo dice `claude --help`), y aquí el hook es lo que se mide. "
         "`--setting-sources project` hace que solo cargue el `.claude/settings.json` del directorio temporal.", "",
         "## Confianza: reglas allow del proyecto en -p", "", "```", *resultados_extra.get("confianza", {}).get("debug", []),
         "stderr: " + resultados_extra.get("confianza", {}).get("stderr", ""), "```", "",
         "## La semilla, tal cual la ven los linters", ""]
    for c, salida in semilla(env):
        L += [f"$ {c}", "```", salida, "```", ""]
    L += ["## El hook solo, sin Claude (JSON por stdin sobre la semilla)", ""]
    for k, rc, err in aislado:
        L += [f"### {k} → exit {rc}", "", "```", err, "```", ""]
    L += ["## Resultados por corrida", "",
          "| tarea | lang | cond | éxito | tarea hecha | Claude corrió verificador | bloqueos del hook | supresiones | tocados | deuda en no tocados | seg | USD |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in sorted(resultados):
        r = resultados[key]
        L.append(f"| {r['tarea']} | {r['lang']} | {r['cond']} | {'sí' if r['exito'] else 'NO'} | {'sí' if r['tarea_hecha'] else 'no'} | "
                 f"{r['verif_por_claude']} | {r['hook_bloqueos']} | {r['supresiones_nuevas']} | {', '.join(r['tocados'])} | "
                 f"{', '.join(r['deuda_en_no_tocados']) or '—'} | {r['segundos']} | {r['costo']:.3f} |")
    L += ["", "## Totales", ""]
    for c, nombre in CONDICIONES.items():
        rs = [r for r in resultados.values() if r["cond"] == c]
        if not rs:
            continue
        L += [f"### {nombre} ({len(rs)} corridas)", "",
              f"- Corridas con todos los archivos tocados limpios: **{sum(r['exito'] for r in rs)}/{len(rs)}**",
              f"- Corridas en que Claude ejecutó un verificador por su cuenta: {sum(r['verif_por_claude'] > 0 for r in rs)}/{len(rs)}",
              f"- Tarea hecha: {sum(r['tarea_hecha'] for r in rs)}/{len(rs)}",
              f"- Supresiones nuevas: {sum(r['supresiones_nuevas'] for r in rs)}",
              f"- Bloqueos del hook (exit 2): {sum(r['hook_bloqueos'] for r in rs)} en {sum(r['hook_bloqueos'] > 0 for r in rs)} corridas",
              f"- Corridas con deuda en archivos que no tocó: {sum(bool(r['deuda_en_no_tocados']) for r in rs)}",
              f"- Tiempo medio: {sum(r['segundos'] for r in rs) / len(rs):.0f} s · costo total: {sum(r['costo'] or 0 for r in rs):.2f} USD", ""]
        for lang in ("go", "py", "sh"):
            sub = [r for r in rs if r["lang"] == lang]
            L.append(f"  - {lang}: {sum(r['exito'] for r in sub)}/{len(sub)} limpias; verificador por su cuenta en {sum(r['verif_por_claude'] > 0 for r in sub)}/{len(sub)}")
        L.append("")
    L += ["## Avisos que quedaron en las corridas que fallaron", ""]
    for key in sorted(resultados):
        r = resultados[key]
        for k, a in r["archivos"].items():
            if not a["pasa"]:
                L += [f"### {key} · {k}", "", "```", a["salida"], "```", ""]
    L += ["## Herramientas que usó Claude (por corrida)", ""]
    for key in sorted(resultados):
        r = resultados[key]
        L += [f"- **{key}** ({r['turnos']} turnos): " + " · ".join(r["llamadas"]), f"  - respuesta: {r['final'][:300]!r}"]
    (AQUI / "SALIDA.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    scripts = asegurar_venv()
    env = entorno(scripts)
    resultados = json.loads(RESULTADOS.read_text(encoding="utf-8")) if RESULTADOS.exists() else {}
    if "--piloto" in sys.argv:
        t = TAREAS[4]
        r = medir(t[0], t[1], t[2], t[3], "B", env, nombre="PILOTO-1-T05-B")
        (AQUI / "piloto.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    if "--informe" not in sys.argv:
        for tid, lang, prompt, esperado in TAREAS:
            for cond in ("A", "B") + (("C", "D") if tid in TAREAS_CD else ()):
                key = f"{tid}-{cond}"
                if key in resultados:
                    continue
                print(f"→ {key}", flush=True)
                resultados[key] = medir(tid, lang, prompt, esperado, cond, env)
                RESULTADOS.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
                r = resultados[key]
                print(f"  éxito={r['exito']} verif={r['verif_por_claude']} hook={r['hook_bloqueos']} {r['segundos']}s {r['costo']}", flush=True)
    extra_path = AQUI / "resultados_extra.json"
    extra = json.loads(extra_path.read_text(encoding="utf-8")) if extra_path.exists() else {}
    if "confianza" not in extra and "--informe" not in sys.argv:
        extra["confianza"] = prueba_confianza(env)
        extra_path.write_text(json.dumps(extra, indent=2, ensure_ascii=False), encoding="utf-8")
    global resultados_extra
    resultados_extra = extra
    informe(resultados, hook_aislado(env), env)
    print("SALIDA.md escrita")


if __name__ == "__main__":
    main()
