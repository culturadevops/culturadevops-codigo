# -*- coding: utf-8 -*-
"""Ejecuta los ejemplos que salen en pantalla en el 704 y los añade al final de SALIDA.md (después de resumen.py)."""
import os
import subprocess

import banco

AQUI = banco.AQUI
M = os.path.join(AQUI, "muestras")


def sh(args):
    r = banco.docker(args)
    return (r.stdout + r.stderr).rstrip()


def main():
    L = ["\n## Ejemplos que salen en pantalla (ejecutados por ejemplos.py)\n"]
    r = banco.ejecutar([("ref", n, f"referencia/{n}.sh") for n in range(1, 51)])
    L.append(f"- Banco: {sum(1 for v in r.values() if v['control'][1] and v['espacios'][1])} /50 referencias OK (control y espacios)")
    r = banco.ejecutar([("neg", 1, "negativos/1.sh"), ("neg", 6, "negativos/6.sh")])
    for k, v in sorted(r.items()):
        L.append(f"- neg {k[1]}: control {'OK' if v['control'][1] else 'FALLA'} · espacios: {v['espacios'][2][:110]}")
    L.append("\n### shellcheck -f gcc · qwen tarea 34, ronda 0\n```")
    L.append(sh(["run", "--rm", "--network", "none", "-v", f"{os.path.join(M, 'qwen', '34')}:/mnt:ro", "-w", "/mnt",
                 banco.SHELLCHECK, "-f", "gcc", "r0.sh"]))
    L.append("```\n\n### shfmt -d · Claude tarea 1 (primeras líneas)\n```")
    L.append("\n".join(sh(["run", "--rm", "--network", "none", "-v", f"{os.path.join(M, 'claude', '01')}:/mnt:ro", "-w", "/mnt",
                           banco.SHFMT, "-d", "r0.sh"]).splitlines()[:10]))
    prueba = ('d=$(mktemp -d); mkdir -p "$d/datos de prueba/sub carpeta"; echo x > "$d/datos de prueba/sub carpeta/a"; '
              'bash /s/muestras/qwen/31/r0.sh "$d/datos de prueba"')
    L.append("```\n\n### qwen tarea 31 con espacios (ShellCheck: 0 avisos)\n```")
    L.append(sh(["run", "--rm", "--network", "none", "-v", f"{AQUI}:/s:ro", banco.RUNNER, "bash", "-c", prueba]))
    L.append("```")
    with open(os.path.join(AQUI, "SALIDA.md"), "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
