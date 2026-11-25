# SALIDA — ¿Python o Node en AWS Lambda? Arranque en frío medido EN LOCAL (cultura-devops 796, 2026-11-05)

⚠️ **No es la nube real.** Es la imagen oficial de Lambda con su emulador (Runtime Interface Emulator, RIE) en Docker, en
esta máquina. El RIE no levanta una microVM Firecracker, no descarga el código, no reparte CPU según la memoria y no tiene la
red de AWS. Sirve para comparar Python con Node en la misma máquina, no como cifra de AWS.

## Versiones
```
$ docker run --rm --entrypoint sh cd-lambda-py:1 -c 'python --version; python -c "import boto3,botocore; ..."'
Python 3.14.10
boto3 1.42.97 botocore 1.42.97
$ docker run --rm --entrypoint sh cd-lambda-node:1 -c 'node --version; grep version .../@aws-sdk/client-s3|client-dynamodb/package.json'
v24.22.2
  "version": "3.1105.0",
  "version": "3.1105.0",
$ ls /usr/local/bin        (en las dos imágenes)
aws-lambda-rie
```
- Bases: `public.ecr.aws/lambda/python:3.14` y `public.ecr.aws/lambda/nodejs:24`. Docker 29.6.2.
- Funciones: `simple` (suma de 10.000 vueltas, sin importar nada) y `sdk` (crea un cliente de S3 y uno de DynamoDB FUERA del
  handler, con el SDK que ya trae la imagen: boto3 en Python, AWS SDK v3 en Node; no llama a AWS).
- Cada contenedor: `docker run -d --rm --cpus 1 --memory 1g`. Corridas con `correr.py funcional` (sin cronómetro) y
  `correr.py medir` con el candado `_logs/banco.lock` tomado (10:50:31 → 10:54:05). 15 contenedores nuevos por variante,
  intercalados python/node, y 30 invocaciones en caliente en cada uno.

## Funcional (sin cronómetro)

```
$ docker image inspect cd-lambda-py:1 (base python:3.14)
  contenido (comprimido): 204.8 MiB
  en disco (docker images): 846MB
$ docker image inspect cd-lambda-node:1 (base nodejs:24)
  contenido (comprimido): 135.8 MiB
  en disco (docker images): 611MB
```

### ¿Llegan las dos al mismo estado? (misma respuesta, sin el campo lang)

```
$ curl -XPOST .../invocations -d '{}'   # python · simple · 1.ª
{"lang": "python", "fn": "simple", "suma": 4804349266, "invocacion": 1}
$ (2.ª en el mismo contenedor)
{"lang": "python", "fn": "simple", "suma": 4804349266, "invocacion": 2}
```

Log del RIE de esa corrida (las líneas REPORT):
```
START RequestId: 1df76c0f-a26e-442e-97af-61c9d3fb197c Version: $LATEST
REPORT RequestId: 1df76c0f-a26e-442e-97af-61c9d3fb197c  Init Duration: 0.02 ms  Duration: 41.67 ms  Billed Duration: 42 ms  Memory Size: 3008 MB  Max Memory Used: 3008 MB
START RequestId: c95f8099-8d2d-44f4-a568-836970b11a51 Version: $LATEST
REPORT RequestId: c95f8099-8d2d-44f4-a568-836970b11a51  Duration: 1.43 ms  Billed Duration: 2 ms  Memory Size: 3008 MB  Max Memory Used: 3008 MB
05 Nov 2026 13:02:57,718 [INFO] (rapid) INIT REPORT(durationMs: 40.285000)
```
```
$ curl -XPOST .../invocations -d '{}'   # node · simple · 1.ª
{"lang":"node","fn":"simple","suma":4804349266,"invocacion":1}
$ (2.ª en el mismo contenedor)
{"lang":"node","fn":"simple","suma":4804349266,"invocacion":2}
```

✅ simple: Python y Node devuelven lo mismo: {'fn': 'simple', 'suma': 4804349266, 'invocacion': 1}

```
$ curl -XPOST .../invocations -d '{}'   # python · sdk · 1.ª
{"lang": "python", "fn": "sdk", "suma": 4804349266, "clientes": ["s3", "dynamodb"], "invocacion": 1}
$ (2.ª en el mismo contenedor)
{"lang": "python", "fn": "sdk", "suma": 4804349266, "clientes": ["s3", "dynamodb"], "invocacion": 2}
```
```
$ curl -XPOST .../invocations -d '{}'   # node · sdk · 1.ª
{"lang":"node","fn":"sdk","suma":4804349266,"clientes":["s3","dynamodb"],"invocacion":1}
$ (2.ª en el mismo contenedor)
{"lang":"node","fn":"sdk","suma":4804349266,"clientes":["s3","dynamodb"],"invocacion":2}
```

✅ sdk: Python y Node devuelven lo mismo: {'fn': 'sdk', 'suma': 4804349266, 'clientes': ['s3', 'dynamodb'], 'invocacion': 1}


## Medición (2026-11-05 10:50) · 15 arranques en frío y 30 en caliente por variante

Columnas: total = `docker run` → 1.ª respuesta (incluye Docker) · 1.ª Duration = lo que el RIE pone en el REPORT
de la 1.ª invocación (ahí dentro va el INIT, porque el RIE inicia en la 1.ª llamada) · caliente = invocaciones 2..N.

| variante | total frío p50 (min-max) ms | INIT REPORT p50 ms | 1.ª Duration p50 ms | caliente Duration p50 ms | caliente ida y vuelta p50 ms | memoria contenedor MiB |
|---|---|---|---|---|---|---|
| python · simple | 234 (223-357) | 27.9 | 29.0 | 0.97 | 13.87 | 15.3 |
| node · simple | 238 (223-358) | 29.3 | 31.7 | 0.55 | 12.10 | 21.8 |
| python · sdk | 372 (356-622) | 164.6 | 165.6 | 0.95 | 14.91 | 51.1 |
| node · sdk | 311 (293-334) | 97.1 | 98.5 | 0.52 | 14.51 | 41.9 |

Crudos (total frío ms, en orden de ronda):
  python·simple: 357 227 228 227 234 232 250 244 255 242 234 249 226 223 236
  node·simple: 358 234 269 238 236 239 242 246 223 238 236 235 230 228 247
  python·sdk: 622 406 381 366 369 383 356 372 379 371 364 368 368 380 419
  node·sdk: 313 321 319 296 297 293 330 306 315 334 307 311 329 296 304
Crudos (INIT REPORT ms):
  python·simple: 88.7 28.3 27.5 27.2 27.1 27.9 28.6 28.4 29.2 28.2 27.0 28.0 27.0 27.0 27.6
  node·simple: 122.7 30.3 33.0 30.9 29.3 28.4 31.6 31.2 29.2 27.3 29.0 28.9 29.5 27.5 28.9
  python·sdk: 410.4 185.6 158.7 161.8 168.8 172.3 161.5 164.6 168.8 160.7 161.1 159.2 157.8 169.1 179.2
  node·sdk: 121.5 95.4 99.9 90.4 96.9 97.4 95.3 97.0 101.5 94.8 98.1 101.5 97.1 97.2 95.7
Crudos (1.ª Duration ms):
  python·simple: 90.4 29.5 28.6 28.3 28.2 29.0 29.8 29.6 30.4 29.2 28.1 29.1 28.1 28.2 28.8
  node·simple: 124.0 31.7 39.1 35.3 33.6 29.6 32.8 35.7 30.4 28.7 30.2 33.2 30.7 28.7 30.0
  python·sdk: 411.6 186.9 159.8 163.2 170.0 173.4 162.8 165.6 170.0 161.9 162.6 160.7 158.9 170.3 180.4
  node·sdk: 123.5 96.8 101.3 91.6 99.4 99.0 96.6 98.3 102.9 97.2 99.4 102.8 98.4 98.5 97.8

## Lo que hay que leer bien
- Ronda 1 (el primer contenedor de cada variante) sale mucho más lenta en las cuatro: python·sdk 622 ms / INIT 410,4 ms. Las
  rondas 2-15 son estables. La causa NO está medida (probable: caché de disco al leer la imagen por primera vez).
- El RIE pone `Init Duration: 0.02 ms` en el REPORT: inicia en la 1.ª invocación, así que el INIT va DENTRO de la 1.ª Duration.
  El INIT de verdad sale en la línea `INIT REPORT(durationMs: ...)`.
- El RIE pone `Max Memory Used: 3008 MB` = `Memory Size: 3008 MB` aunque el contenedor tenga `--memory 1g`: el emulador NO mide
  memoria. La columna de memoria es `docker stats --no-stream` del contenedor entero (RIE incluido), una lectura por contenedor.
- «total frío» incluye crear el contenedor con Docker: no existe así en AWS.
