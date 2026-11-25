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

