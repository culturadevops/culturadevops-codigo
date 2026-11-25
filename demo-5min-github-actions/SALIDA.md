# SALIDA — GitHub Actions en 5 minutos (cultura-devops)

Generado 2026-10-23 12:35 UTC con `python correr.py`. act v0.2.89 con `-P ubuntu-latest=node:22-bookworm-slim`; el secreto es inventado.

## 1 · El workflow

### versión de act

`$ act --version`

```
act version 0.2.89
```
(código de salida 0)

### el archivo

`$ cat .github/workflows/ci.yml`

```
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [20, 22]
    steps:
      - uses: actions/checkout@v4
      - name: tests
        run: |
          echo "probando con node ${{ matrix.node }}"
          test "$(cat precio.txt)" -gt 0 && echo "precio correcto"
  desplegar:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: desplegar
        env:
          CLAVE: ${{ secrets.CLAVE_DESPLIEGUE }}
        run: |
          echo "desplegando con la clave $CLAVE"
          echo "listo"
```
(código de salida 0)

### los trabajos y en qué orden

`$ act -l`

```
Stage  Job ID     Job name   Workflow name  Workflow file  Events
0      test       test       ci             ci.yml         push  
1      desplegar  desplegar  ci             ci.yml         push  
time="2026-10-23T12:35:35Z" level=info msg="Using docker host 'unix:///var/run/docker.sock', and daemon socket 'unix:///var/run/docker.sock'"
```
(código de salida 0)

## 2 · Ejecutarlo

### un push

`$ act push -s CLAVE_DESPLIEGUE=…`

```
✅  Success - Set up job
  ✅  Success - Set up job
  ✅  Success - Main actions/checkout@v4 [24.090558ms]
  ✅  Success - Main actions/checkout@v4 [34.53444ms]
probando con node 20
probando con node 22
precio correcto
precio correcto
  ✅  Success - Main tests [103.663584ms]
  ✅  Success - Main tests [89.25916ms]
  ✅  Success - Complete job
🏁  Job succeeded
  ✅  Success - Complete job
🏁  Job succeeded
  ✅  Success - Set up job
desplegando con la clave ***
listo
  ✅  Success - Main desplegar [67.872476ms]
  ✅  Success - Complete job
🏁  Job succeeded
```
(código de salida 0)

> El secreto aparece como *** en el registro.

## 3 · Un test falla

### precio = 0

`$ act push -s CLAVE_DESPLIEGUE=…`

```
✅  Success - Set up job
  ✅  Success - Main actions/checkout@v4 [16.973994ms]
  ✅  Success - Set up job
  ✅  Success - Main actions/checkout@v4 [19.316585ms]
probando con node 20
  ❌  Failure - Main tests [97.852253ms]
  ✅  Success - Complete job
🏁  Job failed
probando con node 22
  ❌  Failure - Main tests [98.638834ms]
  ✅  Success - Complete job
🏁  Job failed
```
(código de salida 0)

> El trabajo «desplegar» no aparece: depende de «test», que falló.
