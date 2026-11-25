# SALIDA — 711 · Dockerfiles escritos por IA contra hadolint (y lo que pesan)

Generado por `resumen.py` (`crear_apps.py` → `generar.py` → `analizar.py` → `resumen.py`; `ejecutar_todo.py` lo corre todo). Medido el 2026-10-29. **No es un estudio**: 20 apps, un modelo local y Claude Code.

## Montaje

- 20 apps fijadas antes de generar (crear_apps.py): 5 Node, 5 Python, 5 Go, 5 Java. Todas escuchan en 8080 y responden «ok».
- qwen2.5:7b por Ollama, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`, opciones {'temperature': 0.2, 'seed': 42, 'num_ctx': 8192, 'num_predict': 2048}. Las 20 apps.
- Claude Code 2.1.312, `claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --output-format json`, desde un directorio vacío de mktemp, sin herramientas. Modelos informados: ['claude-haiku-5-5', 'claude-opus-5-5']. Las 20 apps. Costo total informado: 0.64 USD; segundos por Dockerfile (r0), media 5.9.
- hadolint 2.14.0 (`hadolint/hadolint:v2.14.0`), `-f json`, todos los niveles. Limpio = 0 avisos.
- Construcción: `docker buildx build` con un builder propio (`v711-builder`, driver docker-container) y `--load`. Tamaño = DISK USAGE de `docker images` (descomprimida). Root = Config.User vacío, root o 0. latest = algún FROM sin etiqueta o con :latest.
- Arranca = `docker run` (--cpus 1, --memory 1g) y curl desde otro contenedor a :8080/ responde «ok» antes de 40 s.
- Bucle: si la ronda k tiene avisos y k<3, la misma IA recibe su Dockerfile, la salida de hadolint y los archivos del proyecto. Se construye y se ejecuta la ronda 0 y la última; las intermedias solo pasan por hadolint. Trampa = cada `# hadolint ignore` nuevo.
- El banco se probó antes con 20 Dockerfiles de referencia escritos a mano (referencia/): ver abajo.

### Prompt (ronda 0)

```
Escribe un Dockerfile de producción para esta aplicación. La aplicación tiene que escuchar en el puerto 8080.
El contexto de construcción es la carpeta del proyecto. Estos son sus archivos:

{archivos}

Responde solo con el Dockerfile completo dentro de un bloque ```dockerfile, sin explicaciones.
```

### Prompt (rondas 1-3)

```
Escribiste este Dockerfile para la aplicación de abajo:
```dockerfile
{dockerfile}
```
hadolint 2.14.0 da estos avisos:
{avisos}

Los archivos del proyecto (el contexto de construcción) son:

{archivos}

Corrige el Dockerfile para que hadolint no dé avisos. Responde solo con el Dockerfile completo dentro de un bloque ```dockerfile, sin explicaciones.
```

## Referencias escritas a mano (prueba del banco)

- Construyen 20/20 · arrancan 20/20 · hadolint con avisos 0 · root 0
| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |
|---|---|---|---|---|---|---|---|---|
| g1-net-http | 0  | sí | sí | 18.9 | 65532 | False | False | golang:1.24.11 gcr.io/distroless/static-debian12:nonroot |
| g2-gin | 0  | sí | sí | 24.7 | 65532 | False | False | golang:1.24.11 gcr.io/distroless/static-debian12:nonroot |
| g3-chi | 0  | sí | sí | 19.5 | 65532 | False | False | golang:1.24.11 gcr.io/distroless/static-debian12:nonroot |
| g4-cmd-internal | 0  | sí | sí | 19.0 | 65532 | False | False | golang:1.24.11 gcr.io/distroless/static-debian12:nonroot |
| g5-embed | 0  | sí | sí | 19.2 | 65532 | False | False | golang:1.24.11 gcr.io/distroless/static-debian12:nonroot |
| j1-maven-sin-dependencias | 0  | sí | sí | 402.0 | 1000 | False | False | maven:3.9.9-eclipse-temurin-21 eclipse-temurin:21.0.5_11-jre |
| j2-spring-boot | 0  | sí | sí | 441.0 | 1000 | False | False | maven:3.9.9-eclipse-temurin-21 eclipse-temurin:21.0.5_11-jre |
| j3-un-archivo | 0  | sí | sí | 402.0 | 1000 | False | False | eclipse-temurin:21.0.5_11-jdk eclipse-temurin:21.0.5_11-jre |
| j4-maven-gson-shade | 0  | sí | sí | 402.0 | 1000 | False | False | maven:3.9.9-eclipse-temurin-21 eclipse-temurin:21.0.5_11-jre |
| j5-javalin | 0  | sí | sí | 413.0 | 1000 | False | False | maven:3.9.9-eclipse-temurin-21 eclipse-temurin:21.0.5_11-jre |
| n1-express | 0  | sí | sí | 330.0 | node | False | False | node:22.12.0-bookworm-slim |
| n2-http-sin-dependencias | 0  | sí | sí | 321.0 | node | False | False | node:22.12.0-bookworm-slim |
| n3-fastify | 0  | sí | sí | 343.0 | node | False | False | node:22.12.0-bookworm-slim |
| n4-typescript | 0  | sí | sí | 330.0 | node | False | False | node:22.12.0-bookworm-slim node:22.12.0-bookworm-slim |
| n5-koa | 0  | sí | sí | 327.0 | node | False | False | node:22.12.0-bookworm-slim |
| p1-flask-gunicorn | 0  | sí | sí | 209.0 | app | False | False | python:3.12.8-slim-bookworm |
| p2-fastapi | 0  | sí | sí | 221.0 | app | False | False | python:3.12.8-slim-bookworm |
| p3-sin-dependencias | 0  | sí | sí | 186.0 | app | False | False | python:3.12.8-slim-bookworm |
| p4-pyproject | 0  | sí | sí | 209.0 | app | False | False | python:3.12.8-slim-bookworm |
| p5-aiohttp | 0  | sí | sí | 216.0 | app | False | False | python:3.12.8-slim-bookworm |

## qwen — 20 apps

- Ronda 0 con al menos un aviso de hadolint: **8 de 20**; avisos: 11 · por código: {'DL3007': 5, 'DL3045': 4, 'DL3008': 1, 'DL3015': 1}
- Ronda 0: construyen 13/20 · arrancan y responden 8/20 · corren como root 13 de 13 construidas ['n1-express', 'n2-http-sin-dependencias', 'n3-fastify', 'n4-typescript', 'n5-koa', 'p1-flask-gunicorn', 'p2-fastapi', 'p3-sin-dependencias', 'p4-pyproject', 'p5-aiohttp', 'g1-net-http', 'g2-gin', 'g3-chi'] · usan latest 5 ['g1-net-http', 'g2-gin', 'g3-chi', 'g4-cmd-internal', 'g5-embed']
  - No construyen: ['g4-cmd-internal', 'g5-embed', 'j1-maven-sin-dependencias', 'j2-spring-boot', 'j3-un-archivo', 'j4-maven-gson-shade', 'j5-javalin']
  - Construyen y no arrancan: ['n3-fastify', 'p4-pyproject', 'g1-net-http', 'g2-gin', 'g3-chi']
  - Disco (MB), mediana por lenguaje: Node 232.0 (n=5), Python 212.0 (n=5), Go 26.3 (n=3)
- Última ronda: construyen 13/20 · arrancan y responden 8/20 · corren como root 13 de 13 construidas ['n1-express', 'n2-http-sin-dependencias', 'n3-fastify', 'n4-typescript', 'n5-koa', 'p1-flask-gunicorn', 'p2-fastapi', 'p3-sin-dependencias', 'p4-pyproject', 'p5-aiohttp', 'g1-net-http', 'g2-gin', 'g3-chi'] · usan latest 0 []
  - No construyen: ['g4-cmd-internal', 'g5-embed', 'j1-maven-sin-dependencias', 'j2-spring-boot', 'j3-un-archivo', 'j4-maven-gson-shade', 'j5-javalin']
  - Construyen y no arrancan: ['n3-fastify', 'p4-pyproject', 'g1-net-http', 'g2-gin', 'g3-chi']
  - Disco (MB), mediana por lenguaje: Node 232.0 (n=5), Python 212.0 (n=5), Go 24.9 (n=3)
- Imágenes base en ronda 0: {'golang:1.24': 5, 'alpine:latest': 5, 'node:16-alpine': 2, 'node:14': 2, 'python:3.11-slim': 2, 'python:3.9-slim': 2, 'node:18-alpine': 1, 'python:3.10-slim': 1, 'openjdk:17-jdk-alpine': 1, 'openjdk:21-jdk-slim': 1, 'openjdk:17-alpine': 1, 'openjdk:17-jdk-slim': 1, 'openjdk:21-jdk-alpine': 1}
- Bucle IA + hadolint sobre 8: {'limpio en ronda 1': 7, 'limpio en ronda 2': 1}
- Supresiones nuevas (# hadolint ignore): ninguna
- Antes → después del bucle:
  - g1-net-http: construye True→True, arranca False→False, root True→True, disco 25.8→24.4
  - g2-gin: construye True→True, arranca False→False, root True→True, disco 31.6→30.1
  - g3-chi: construye True→True, arranca False→False, root True→True, disco 26.3→24.9
  - g4-cmd-internal: construye False→False, arranca None→None, root None→None, disco None→None
  - g5-embed: construye False→False, arranca None→None, root None→None, disco None→None
  - j2-spring-boot: construye False→False, arranca None→None, root None→None, disco None→None
  - j4-maven-gson-shade: construye False→False, arranca None→None, root None→None, disco None→None
  - j5-javalin: construye False→False, arranca None→None, root None→None, disco None→None

### Ronda 0

| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |
|---|---|---|---|---|---|---|---|---|
| g1-net-http | 1 DL3007 | sí | NO | 25.8 |  | True | True | golang:1.24 alpine:latest |
| g2-gin | 1 DL3007 | sí | NO | 31.6 |  | True | True | golang:1.24 alpine:latest |
| g3-chi | 1 DL3007 | sí | NO | 26.3 |  | True | True | golang:1.24 alpine:latest |
| g4-cmd-internal | 1 DL3007 | NO | — |  |  |  | True | golang:1.24 alpine:latest |
| g5-embed | 3 DL3007,DL3045 | NO | — |  |  |  | True | golang:1.24 alpine:latest |
| j1-maven-sin-dependencias | 0  | NO | — |  |  |  | False | openjdk:17-jdk-alpine |
| j2-spring-boot | 2 DL3008,DL3015 | NO | — |  |  |  | False | openjdk:21-jdk-slim |
| j3-un-archivo | 0  | NO | — |  |  |  | False | openjdk:17-alpine |
| j4-maven-gson-shade | 1 DL3045 | NO | — |  |  |  | False | openjdk:17-jdk-slim |
| j5-javalin | 1 DL3045 | NO | — |  |  |  | False | openjdk:21-jdk-alpine |
| n1-express | 0  | sí | sí | 182.0 |  | True | False | node:16-alpine |
| n2-http-sin-dependencias | 0  | sí | sí | 1350.0 |  | True | False | node:14 |
| n3-fastify | 0  | sí | NO | 195.0 |  | True | False | node:16-alpine |
| n4-typescript | 0  | sí | sí | 232.0 |  | True | False | node:18-alpine |
| n5-koa | 0  | sí | sí | 1360.0 |  | True | False | node:14 |
| p1-flask-gunicorn | 0  | sí | sí | 212.0 |  | True | False | python:3.11-slim |
| p2-fastapi | 0  | sí | sí | 216.0 |  | True | False | python:3.10-slim |
| p3-sin-dependencias | 0  | sí | sí | 183.0 |  | True | False | python:3.9-slim |
| p4-pyproject | 0  | sí | NO | 215.0 |  | True | False | python:3.11-slim |
| p5-aiohttp | 0  | sí | sí | 209.0 |  | True | False | python:3.9-slim |

### Última ronda

| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |
|---|---|---|---|---|---|---|---|---|
| g1-net-http | 0  | sí | NO | 24.4 |  | True | False | golang:1.24 alpine:3.19 |
| g2-gin | 0  | sí | NO | 30.1 |  | True | False | golang:1.24 alpine:3.18 |
| g3-chi | 0  | sí | NO | 24.9 |  | True | False | golang:1.24 alpine:3.18 |
| g4-cmd-internal | 0  | NO | — |  |  |  | False | golang:1.24 alpine:3.19.0 |
| g5-embed | 0  | NO | — |  |  |  | False | golang:1.24 alpine:3.18.2 |
| j1-maven-sin-dependencias | 0  | NO | — |  |  |  | False | openjdk:17-jdk-alpine |
| j2-spring-boot | 0  | NO | — |  |  |  | False | openjdk:21-jdk-slim |
| j3-un-archivo | 0  | NO | — |  |  |  | False | openjdk:17-alpine |
| j4-maven-gson-shade | 0  | NO | — |  |  |  | False | openjdk:17-jdk-slim |
| j5-javalin | 0  | NO | — |  |  |  | False | openjdk:21-jdk-alpine |
| n1-express | 0  | sí | sí | 182.0 |  | True | False | node:16-alpine |
| n2-http-sin-dependencias | 0  | sí | sí | 1350.0 |  | True | False | node:14 |
| n3-fastify | 0  | sí | NO | 195.0 |  | True | False | node:16-alpine |
| n4-typescript | 0  | sí | sí | 232.0 |  | True | False | node:18-alpine |
| n5-koa | 0  | sí | sí | 1360.0 |  | True | False | node:14 |
| p1-flask-gunicorn | 0  | sí | sí | 212.0 |  | True | False | python:3.11-slim |
| p2-fastapi | 0  | sí | sí | 216.0 |  | True | False | python:3.10-slim |
| p3-sin-dependencias | 0  | sí | sí | 183.0 |  | True | False | python:3.9-slim |
| p4-pyproject | 0  | sí | NO | 215.0 |  | True | False | python:3.11-slim |
| p5-aiohttp | 0  | sí | sí | 209.0 |  | True | False | python:3.9-slim |

## claude — 20 apps

- Ronda 0 con al menos un aviso de hadolint: **3 de 20**; avisos: 3 · por código: {'DL3018': 2, 'DL3013': 1}
- Ronda 0: construyen 20/20 · arrancan y responden 20/20 · corren como root 0 de 20 construidas [] · usan latest 0 []
  - No construyen: []
  - Construyen y no arrancan: []
  - Disco (MB), mediana por lenguaje: Node 244.0 (n=5), Python 201.0 (n=5), Go 14.2 (n=5), Java 326.0 (n=5)
- Última ronda: construyen 20/20 · arrancan y responden 20/20 · corren como root 0 de 20 construidas [] · usan latest 0 []
  - No construyen: []
  - Construyen y no arrancan: []
  - Disco (MB), mediana por lenguaje: Node 244.0 (n=5), Python 201.0 (n=5), Go 14.2 (n=5), Java 326.0 (n=5)
- Imágenes base en ronda 0: {'node:22-alpine': 10, 'python:3.12-slim': 6, 'gcr.io/distroless/static-debian12:nonroot': 5, 'golang:1.24-alpine': 4, 'maven:3.9-eclipse-temurin-21': 4, 'eclipse-temurin:21-jre-alpine': 3, 'python:${PYTHON_VERSION}-slim': 2, 'eclipse-temurin:21-jre': 2, 'golang:1.24': 1, 'eclipse-temurin:21-jdk-alpine': 1}
- Bucle IA + hadolint sobre 3: {'limpio en ronda 1': 3}
- Supresiones nuevas (# hadolint ignore): ninguna
- Antes → después del bucle:
  - n2-http-sin-dependencias: construye True→True, arranca True→True, root False→False, disco 239.0→230.0
  - n5-koa: construye True→True, arranca True→True, root False→False, disco 243.0→233.0
  - p4-pyproject: construye True→True, arranca True→True, root False→False, disco 201.0→201.0

### Ronda 0

| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |
|---|---|---|---|---|---|---|---|---|
| g1-net-http | 0  | sí | sí | 14.1 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g2-gin | 0  | sí | sí | 17.6 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g3-chi | 0  | sí | sí | 14.4 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g4-cmd-internal | 0  | sí | sí | 14.1 | nonroot:nonroot | False | False | golang:1.24 gcr.io/distroless/static-debian12:nonroot |
| g5-embed | 0  | sí | sí | 14.2 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| j1-maven-sin-dependencias | 0  | sí | sí | 456.0 | 10001:10001 | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre |
| j2-spring-boot | 0  | sí | sí | 326.0 | app | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre-alpine |
| j3-un-archivo | 0  | sí | sí | 286.0 | app | False | False | eclipse-temurin:21-jdk-alpine eclipse-temurin:21-jre-alpine |
| j4-maven-gson-shade | 0  | sí | sí | 457.0 | 10001:10001 | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre |
| j5-javalin | 0  | sí | sí | 297.0 | app | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre-alpine |
| n1-express | 0  | sí | sí | 244.0 | node | False | False | node:22-alpine node:22-alpine |
| n2-http-sin-dependencias | 1 DL3018 | sí | sí | 239.0 | node | False | False | node:22-alpine |
| n3-fastify | 0  | sí | sí | 256.0 | node | False | False | node:22-alpine node:22-alpine |
| n4-typescript | 0  | sí | sí | 244.0 | node | False | False | node:22-alpine node:22-alpine node:22-alpine |
| n5-koa | 1 DL3018 | sí | sí | 243.0 | node | False | False | node:22-alpine node:22-alpine |
| p1-flask-gunicorn | 0  | sí | sí | 187.0 | app | False | False | python:3.12-slim |
| p2-fastapi | 0  | sí | sí | 217.0 | app | False | False | python:3.12-slim python:3.12-slim |
| p3-sin-dependencias | 0  | sí | sí | 177.0 | app | False | False | python:3.12-slim |
| p4-pyproject | 1 DL3013 | sí | sí | 201.0 | app | False | False | python:${PYTHON_VERSION}-slim python:${PYTHON_VERSION}-slim |
| p5-aiohttp | 0  | sí | sí | 211.0 | app | False | False | python:3.12-slim python:3.12-slim |

### Última ronda

| app | hadolint | construye | arranca | disco MB | usuario | root | latest | bases |
|---|---|---|---|---|---|---|---|---|
| g1-net-http | 0  | sí | sí | 14.1 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g2-gin | 0  | sí | sí | 17.6 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g3-chi | 0  | sí | sí | 14.4 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| g4-cmd-internal | 0  | sí | sí | 14.1 | nonroot:nonroot | False | False | golang:1.24 gcr.io/distroless/static-debian12:nonroot |
| g5-embed | 0  | sí | sí | 14.2 | nonroot:nonroot | False | False | golang:1.24-alpine gcr.io/distroless/static-debian12:nonroot |
| j1-maven-sin-dependencias | 0  | sí | sí | 456.0 | 10001:10001 | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre |
| j2-spring-boot | 0  | sí | sí | 326.0 | app | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre-alpine |
| j3-un-archivo | 0  | sí | sí | 286.0 | app | False | False | eclipse-temurin:21-jdk-alpine eclipse-temurin:21-jre-alpine |
| j4-maven-gson-shade | 0  | sí | sí | 457.0 | 10001:10001 | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre |
| j5-javalin | 0  | sí | sí | 297.0 | app | False | False | maven:3.9-eclipse-temurin-21 eclipse-temurin:21-jre-alpine |
| n1-express | 0  | sí | sí | 244.0 | node | False | False | node:22-alpine node:22-alpine |
| n2-http-sin-dependencias | 0  | sí | sí | 230.0 | node | False | False | node:22-alpine3.22 |
| n3-fastify | 0  | sí | sí | 256.0 | node | False | False | node:22-alpine node:22-alpine |
| n4-typescript | 0  | sí | sí | 244.0 | node | False | False | node:22-alpine node:22-alpine node:22-alpine |
| n5-koa | 0  | sí | sí | 233.0 | node | False | False | node:22-alpine3.22 node:22-alpine3.22 |
| p1-flask-gunicorn | 0  | sí | sí | 187.0 | app | False | False | python:3.12-slim |
| p2-fastapi | 0  | sí | sí | 217.0 | app | False | False | python:3.12-slim python:3.12-slim |
| p3-sin-dependencias | 0  | sí | sí | 177.0 | app | False | False | python:3.12-slim |
| p4-pyproject | 0  | sí | sí | 201.0 | app | False | False | python:${PYTHON_VERSION}-slim python:${PYTHON_VERSION}-slim |
| p5-aiohttp | 0  | sí | sí | 211.0 | app | False | False | python:3.12-slim python:3.12-slim |

## Versión del lenguaje fuera de soporte (endoflife.date/api, consultado 2026-10-29)

- qwen: 8 → ['n1-express (node:16-alpine, fin 2023-09-11)', 'n2-http-sin-dependencias (node:14, fin 2023-04-30)', 'n3-fastify (node:16-alpine, fin 2023-09-11)', 'n4-typescript (node:18-alpine, fin 2025-04-30)', 'n5-koa (node:14, fin 2023-04-30)', 'p2-fastapi (python:3.10-slim, fin 2026-10-01)', 'p3-sin-dependencias (python:3.9-slim, fin 2025-10-31)', 'p5-aiohttp (python:3.9-slim, fin 2025-10-31)']
- claude: 0 → []

## Diagnóstico (diagnostico.py)

- qwen n3-fastify r0: exited exit=1 · TypeError: diagnostics.tracingChannel is not a function
- qwen p4-pyproject r0: exited exit=1 · /usr/local/bin/python: No module named servicio
- qwen g1-net-http r0: exited exit=255 · exec ./servidor: no such file or directory
- qwen g1-net-http r1: exited exit=255 · exec ./servidor: no such file or directory
- qwen g2-gin r0: exited exit=255 · exec ./api-gin: no such file or directory
- qwen g2-gin r1: exited exit=255 · exec ./api-gin: no such file or directory
- qwen g3-chi r0: exited exit=255 · exec ./api-chi: no such file or directory
- qwen g3-chi r1: exited exit=255 · exec ./api-chi: no such file or directory
- docker manifest inspect openjdk:17-jdk-alpine: no such manifest: docker.io/library/openjdk:17-jdk-alpine
- docker manifest inspect openjdk:21-jdk-slim: no such manifest: docker.io/library/openjdk:21-jdk-slim
- docker manifest inspect openjdk:17-alpine: no such manifest: docker.io/library/openjdk:17-alpine
- docker manifest inspect openjdk:17-jdk-slim: no such manifest: docker.io/library/openjdk:17-jdk-slim
- docker manifest inspect openjdk:21-jdk-alpine: no such manifest: docker.io/library/openjdk:21-jdk-alpine

## Revisión mínima (revision_minima.py, app n2, Dockerfile de Claude Code ronda 1)

```
$ hadolint Dockerfile
(sin salida = 0 avisos)
$ docker build -t v711-mi-app .
sha256:d2bb51adf3edcc0d8c96ba9b47164c84a9bcf5dedfca02630eafaebfbe23f330
$ docker run --rm -d -p 18711:8080 --name v711-prueba v711-mi-app
cb37b0aa3c4e57a55b814acf9f2fffb4d4d504e84c82d3d403ab4d264b523bef
$ curl -s localhost:18711/
ok
$ docker image inspect -f '{{.Config.User}}' v711-mi-app
node
$ docker images v711-mi-app
IMAGE                ID             DISK USAGE   CONTENT SIZE   EXTRA
v711-mi-app:latest   d2bb51adf3ed        230MB         57.4MB   U
```
