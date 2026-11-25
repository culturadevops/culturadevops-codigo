# SALIDA — Cloudflare en local (vídeo 412)

Generado 2026-10-13 22:01 UTC con `python correr.py`. Sin cuenta: `wrangler dev` corre el Worker en workerd, el mismo runtime de Cloudflare.

## 1 · La herramienta

### versión de wrangler

`$ npx wrangler --version`

```
4.150.0
```
(código de salida 0)

### el Worker

`$ cat src/index.js; wc -l src/index.js`

```
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/subir") {
      await env.FOTOS.put("foto.txt", "hola desde R2 local");
      return new Response("subido\n");
    }
    if (url.pathname === "/pedido") {
      await env.DB.exec("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, producto TEXT)");
      await env.DB.prepare("INSERT INTO pedidos (producto) VALUES (?)").bind("camiseta").run();
      const { results } = await env.DB.prepare("SELECT COUNT(*) AS n FROM pedidos").all();
      return new Response(`pedidos en D1: ${results[0].n}
`);
    }
    if (url.pathname === "/foto") {
      const obj = await env.FOTOS.get("foto.txt");
      return new Response(obj ? (await obj.text()) + "\n" : "no existe\n", { status: obj ? 200 : 404 });
    }
    const n = Number((await env.VISITAS.get("n")) || 0) + 1;
    await env.VISITAS.put("n", String(n));
    return new Response(`hola desde un Worker · visita ${n}\n`);
  },
};
23 src/index.js
```
(código de salida 0)

### la configuración

`$ cat wrangler.toml`

```
name = "hola-2027"
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
```
(código de salida 0)

## 2 · En marcha, en local

### lo que dice wrangler dev

`$ npx wrangler dev`

```
Your Worker has access to the following bindings:
env.VISITAS (local)       KV Namespace      local
env.DB (tienda)           D1 Database       local
env.FOTOS (fotos)         R2 Bucket         local
⎔ Starting local server...
[wrangler:info] Ready on http://0.0.0.0:8787
```
(código de salida 0)

### tres visitas: el contador vive en KV

`$ curl -s localhost:8787/  (x3)`

```
hola desde un Worker · visita 1
hola desde un Worker · visita 2
hola desde un Worker · visita 3
```
(código de salida 0)

### R2 local: subir y leer

`$ curl -s localhost:8787/subir; curl -s localhost:8787/foto`

```
subido
hola desde R2 local
```
(código de salida 0)

### D1 local: SQL de verdad (SQLite)

`$ curl -s localhost:8787/pedido  (x2)`

```
pedidos en D1: 1
pedidos en D1: 2
```
(código de salida 0)

### lo que tarda en local

`$ curl -w '%{time_total}' (x5)`

```
0.005435 s
0.004225 s
0.004376 s
0.004835 s
0.004019 s
```
(código de salida 0)

> Tiempos en local, sin red: no dicen nada de lo que tarda en Cloudflare.

### dónde guarda el estado local

`$ ls .wrangler/state/v3`

```
cache
d1
kv
observability
r2
```
(código de salida 0)

## 3 · Lo que pesa

### node_modules

`$ du -sh node_modules`

```
209M	node_modules
```
(código de salida 0)
