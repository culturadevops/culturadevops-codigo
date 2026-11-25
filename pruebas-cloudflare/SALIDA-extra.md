# SALIDA extra — Cloudflare en local (vídeo 412)

Generado 2026-10-13 22:09 UTC con `python correr_extra.py`.

## 1 · Mirar lo guardado, desde la CLI

### KV: el valor del contador

`$ npx wrangler kv key get n --binding VISITAS --local`

```
8
```
(código de salida 0)

### R2: el archivo

`$ npx wrangler r2 object get fotos/foto.txt --local --pipe`

```
hola desde R2 local
```
(código de salida 0)

### D1: la tabla, con SQL

`$ npx wrangler d1 execute tienda --local --command 'SELECT id, producto FROM pedidos'`

```
"id": 1,
        "producto": "camiseta"
        "id": 2,
        "producto": "camiseta"
```
(código de salida 0)

## 2 · Lo que se subiría, sin cuenta

### wrangler deploy --dry-run

`$ npx wrangler deploy --dry-run --outdir dist`

```
Total Upload: 1.06 KiB / gzip: 0.56 KiB
Your Worker has access to the following bindings:
env.VISITAS (local)       KV Namespace      
env.DB (tienda)           D1 Database       
env.FOTOS (fotos)         R2 Bucket         
--dry-run: exiting now.
```
(código de salida 0)

### el paquete

`$ ls -l dist`

```
110 README.md
1083 index.js
1950 index.js.map
```
(código de salida 0)
