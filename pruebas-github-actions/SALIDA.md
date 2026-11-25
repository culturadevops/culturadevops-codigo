# SALIDA — GitHub Actions (vídeo 406)

Generado 2026-10-13 20:39 UTC con `python correr.py`.

## 1 · Ejecutar un workflow sin subir nada

### la versión de act

`$ act --version`

```
act version 0.2.89
```
(código de salida 0)

### el workflow

`$ cat .github/workflows/ci.yml`

```
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: tests
        run: |
          echo "probando con la version ${{ matrix.version }}"
          test -f app.txt && echo "app.txt encontrado"
  despliegue:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "solo llego aqui si los tests pasan"
```
(código de salida 0)

### qué trabajos hay

`$ act -l`

```
Stage  Job ID      Job name    Workflow name  Workflow file  Events
0      test        test        ci             ci.yml         push  
1      despliegue  despliegue  ci             ci.yml         push  
time="2026-10-13T20:39:17Z" level=info msg="Using docker host 'unix:///var/run/docker.sock', and daemon socket 'unix:///var/run/docker.sock'"
```
(código de salida 0)

### ejecutarlo en local

`$ act push -P ubuntu-latest=catthehacker/ubuntu:act-latest`

```
✅  Success - Set up job
  ✅  Success - Set up job
  ✅  Success - Main actions/checkout@v4 [21.531609ms]
  ✅  Success - Main actions/checkout@v4 [35.390076ms]
  | probando con la version 3.12
  | app.txt encontrado
  | probando con la version 3.13
  | app.txt encontrado
  ✅  Success - Main tests [123.778663ms]
  ✅  Success - Main tests [113.103013ms]
  ✅  Success - Complete job
🏁  Job succeeded
  ✅  Success - Complete job
🏁  Job succeeded
  ✅  Success - Set up job
⭐ Run Main echo "solo llego aqui si los tests pasan"
  | solo llego aqui si los tests pasan
  ✅  Success - Main echo "solo llego aqui si los tests pasan" [79.220866ms]
  ✅  Success - Complete job
🏁  Job succeeded
```
(código de salida 0)

### y si un test falla

`$ rm app.txt; act push …`

```
✅  Success - Set up job
  ✅  Success - Set up job
  ✅  Success - Main actions/checkout@v4 [16.688762ms]
  ✅  Success - Main actions/checkout@v4 [22.460318ms]
  | probando con la version 3.13
  ❌  Failure - Main tests [93.911234ms]
  | probando con la version 3.12
  ❌  Failure - Main tests [71.306692ms]
  ✅  Success - Complete job
🏁  Job failed
  ✅  Success - Complete job
🏁  Job failed
```
(código de salida 0)

> El trabajo «despliegue» no aparece: depende de «test», que falló.

## 2 · Una etiqueta de action se mueve

### actions/checkout: v4 y sus versiones 4.x

`$ git ls-remote --tags https://github.com/actions/checkout | grep v4`

```
11d5960a326750d5838078e36cf38b85af677262	refs/tags/v4
08eba0b27e820071cde6df949e0beb9ba4906955	refs/tags/v4.3.0
34e114876b0b11c390a56381ad16ebd13914f8d5	refs/tags/v4.3.1
11d5960a326750d5838078e36cf38b85af677262	refs/tags/v4.4.0
```
(código de salida 0)

### y la v5

`$ git ls-remote --tags https://github.com/actions/checkout | grep v5`

```
fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09	refs/tags/v5
93cb6efe18208431cddfb8368fd83d5badbf9bfd	refs/tags/v5.0.1
fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09	refs/tags/v5.1.0
```
(código de salida 0)
