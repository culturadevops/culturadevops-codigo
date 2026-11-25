# -*- coding: utf-8 -*-
"""Banco del vídeo 412 «¿Vale la pena Cloudflare en 2027?». Sin cuenta de Cloudflare: wrangler dev en local
(el mismo runtime, workerd), en un contenedor node:22-slim.
  · un Worker que responde y cuenta visitas en KV;
  · R2 local: guardar un objeto y leerlo;
  · lo que tarda en responder, medido con curl.
    python correr.py   -> SALIDA.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
WRANGLER = """name = "hola-2027"
main = "src/index.js"
compatibility_date = "2026-09-01"

[[kv_namespaces]]
binding = "VISITAS"
id = "local"

[[r2_buckets]]
binding = "FOTOS"
bucket_name = "fotos"

[[d1_databases]]
binding = "DB"
database_name = "tienda"
database_id = "local"
"""
INDEX = """export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/subir") {
      await env.FOTOS.put("foto.txt", "hola desde R2 local");
      return new Response("subido\\n");
    }
    if (url.pathname === "/pedido") {
      await env.DB.exec("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, producto TEXT)");
      await env.DB.prepare("INSERT INTO pedidos (producto) VALUES (?)").bind("camiseta").run();
      const { results } = await env.DB.prepare("SELECT COUNT(*) AS n FROM pedidos").all();
      return new Response(`pedidos en D1: ${results[0].n}\n`);
    }
    if (url.pathname === "/foto") {
      const obj = await env.FOTOS.get("foto.txt");
      return new Response(obj ? (await obj.text()) + "\\n" : "no existe\\n", { status: obj ? 200 : 404 });
    }
    const n = Number((await env.VISITAS.get("n")) || 0) + 1;
    await env.VISITAS.put("n", String(n));
    return new Response(`hola desde un Worker · visita ${n}\\n`);
  },
};
"""


def run(args, timeout=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd, timeout=None):
    return run(["docker", "exec", "-w", "/work", "cflab", "bash", "-c", cmd], timeout)


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    run(["docker", "rm", "-f", "cflab"])
    run(["docker", "run", "-d", "--name", "cflab", "node:22-slim", "bash", "-c", "mkdir -p /work && sleep infinity"])
    ex("apt-get update -qq >/dev/null && apt-get install -y -qq curl ca-certificates >/dev/null 2>&1; "
       "cd /work && npm init -y >/dev/null && npm install --silent wrangler@4 >/dev/null 2>&1; echo listo", timeout=900)
    ex(f"mkdir -p src && cat > wrangler.toml <<'EOF'\n{WRANGLER}EOF\ncat > src/index.js <<'EOF'\n{INDEX}EOF")
    OUT.append(f"# SALIDA — Cloudflare en local (vídeo 412)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               "`python correr.py`. Sin cuenta: `wrangler dev` corre el Worker en workerd, el mismo runtime de Cloudflare.\n")

    OUT.append("## 1 · La herramienta\n")
    bloque("versión de wrangler", "npx wrangler --version", "npx wrangler --version 2>&1 | grep -v '^$' | tail -2")
    bloque("el Worker", "cat src/index.js; wc -l src/index.js", "cat src/index.js; wc -l src/index.js")
    bloque("la configuración", "cat wrangler.toml", "cat wrangler.toml")

    OUT.append("## 2 · En marcha, en local\n")
    ex("nohup npx wrangler dev --ip 0.0.0.0 --port 8787 > dev.log 2>&1 &")
    for _ in range(60):
        s, _ = ex("curl -s -o /dev/null -w '%{http_code}' http://localhost:8787/foto")
        if s in ("200", "404"):
            break
        time.sleep(2)
    bloque("lo que dice wrangler dev", "npx wrangler dev", "grep -E 'Ready|Your Worker has access|env\\.|local' dev.log | sed 's/\\x1b\\[[0-9;]*m//g' | head -12")
    bloque("tres visitas: el contador vive en KV", "curl -s localhost:8787/  (x3)",
           "for i in 1 2 3; do curl -s http://localhost:8787/; done")
    bloque("R2 local: subir y leer", "curl -s localhost:8787/subir; curl -s localhost:8787/foto",
           "curl -s http://localhost:8787/subir; curl -s http://localhost:8787/foto")
    bloque("D1 local: SQL de verdad (SQLite)", "curl -s localhost:8787/pedido  (x2)",
           "for i in 1 2; do curl -s http://localhost:8787/pedido; done")
    bloque("lo que tarda en local", "curl -w '%{time_total}' (x5)",
           "for i in 1 2 3 4 5; do curl -s -o /dev/null -w '%{time_total} s\\n' http://localhost:8787/; done",
           "Tiempos en local, sin red: no dicen nada de lo que tarda en Cloudflare.")
    bloque("dónde guarda el estado local", "ls .wrangler/state/v3", "ls .wrangler/state/v3")

    OUT.append("## 3 · Lo que pesa\n")
    bloque("node_modules", "du -sh node_modules", "du -sh node_modules")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
