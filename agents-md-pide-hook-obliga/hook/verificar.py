"""Hook PostToolUse (matcher Edit|Write) del vídeo 708.

Lee de stdin el JSON que manda Claude Code, saca tool_input.file_path y pasa el
verificador según la extensión. Si hay avisos, los escribe en stderr y sale con
código 2: según la documentación de hooks, en PostToolUse eso «Shows stderr to
Claude; the tool already ran». Si no, sale con 0 y Claude no ve nada.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def correr(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def verificar(ruta: Path):
    ext = ruta.suffix
    if ext == ".go":
        moddir = ruta.parent
        _, salida = correr(["gofmt", "-l", str(ruta)])
        if salida:
            _, diff = correr(["gofmt", "-d", str(ruta)])
            return f"gofmt: el archivo no está formateado\n{diff}"
        rc, salida = correr(["go", "vet", "./..."], cwd=moddir)
        return f"go vet:\n{salida}" if rc else ""
    if ext == ".py":
        rc, salida = correr(["ruff", "check", "--no-cache", str(ruta)])
        return f"ruff:\n{salida}" if rc else ""
    if ext == ".sh":
        rc, salida = correr(["shellcheck", str(ruta)])
        return f"shellcheck:\n{salida}" if rc else ""
    return ""


def main():
    sys.stderr.reconfigure(encoding="utf-8")
    datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    ruta = Path(datos.get("tool_input", {}).get("file_path", ""))
    problema = verificar(ruta) if ruta.is_file() else ""
    registro = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "hooks" / "registro.log"
    registro.parent.mkdir(parents=True, exist_ok=True)
    with open(registro, "a", encoding="utf-8") as f:
        f.write(json.dumps({"archivo": ruta.name, "bloquea": bool(problema)}) + "\n")
    if problema:
        print(f"{ruta.name} no pasa el verificador. Corrígelo sin desactivar avisos:\n{problema}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
