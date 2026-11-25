# -*- coding: utf-8 -*-
"""Banco extra del vídeo 412 (necesita el contenedor cflab de correr.py, con su estado local).
  · mirar lo guardado desde la CLI: KV, R2 y D1 en local;
  · wrangler deploy --dry-run: lo que se subiría, sin cuenta.
    python correr_extra.py   -> SALIDA-extra.md
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "cflab", "bash", "-c", cmd + " 2>&1 | sed 's/\\x1b\\[[0-9;]*m//g' | grep -v '^$'"])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")


def main():
    ex("pkill -f 'wrangler dev' || true")
    OUT.append(f"# SALIDA extra — Cloudflare en local (vídeo 412)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`.\n")
    OUT.append("## 1 · Mirar lo guardado, desde la CLI\n")
    bloque("KV: el valor del contador", "npx wrangler kv key get n --binding VISITAS --local",
           "npx wrangler kv key get n --binding VISITAS --local | tail -1")
    bloque("R2: el archivo", "npx wrangler r2 object get fotos/foto.txt --local --pipe",
           "npx wrangler r2 object get fotos/foto.txt --local --pipe | tail -1")
    bloque("D1: la tabla, con SQL", "npx wrangler d1 execute tienda --local --command 'SELECT id, producto FROM pedidos'",
           "npx wrangler d1 execute tienda --local --command 'SELECT id, producto FROM pedidos' | grep -E '\"id\"|\"producto\"'")
    OUT.append("## 2 · Lo que se subiría, sin cuenta\n")
    bloque("wrangler deploy --dry-run", "npx wrangler deploy --dry-run --outdir dist",
           "npx wrangler deploy --dry-run --outdir dist | grep -E 'Total Upload|bindings|env\\.|dry-run'")
    bloque("el paquete", "ls -l dist", "ls -l dist | awk 'NR>1{print $5, $9}'")
    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
