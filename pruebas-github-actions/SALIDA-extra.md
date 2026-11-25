# SALIDA extra — GitHub Actions (vídeo 406)

Generado 2026-10-13 20:58 UTC con `python correr_extra.py`.

## 1 · actionlint: los errores, antes del push

### la versión de actionlint

`$ actionlint --version`

```
1.7.12
installed by building from source
built with go1.26.1 compiler for linux/amd64
Unable to find image 'rhysd/actionlint:latest' locally
latest: Pulling from rhysd/actionlint
b6b4b7b0e257: Pulling fs layer
4ccd7d76ca98: Pulling fs layer
c09af8888d6a: Pulling fs layer
402b0b0a10fa: Download complete
c09af8888d6a: Download complete
c09af8888d6a: Pull complete
4ccd7d76ca98: Download complete
4ccd7d76ca98: Pull complete
b6b4b7b0e257: Download complete
b6b4b7b0e257: Pull complete
Digest: sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667
Status: Downloaded newer image for rhysd/actionlint:latest
```
(código de salida 0)

### un workflow con dos erratas

`$ actionlint roto.yml`

```
<stdin>:7:32: property "versoin" is not defined in object type {} [expression]
<stdin>:8:3: job "despliegue" needs job "tset" which does not exist in this workflow [job-needs]
```
(código de salida 1)

> matrix.versoin (en lugar de version) y needs: tset (en lugar de test).

## 2 · Los secretos salen enmascarados

### ejecutar con un secreto

`$ act push -s TOKEN=supersecreto123 …`

```
✅  Success - Set up job
⭐ Run Main echo "el token es ***"
  | el token es ***
  ✅  Success - Main echo "el token es ***" [77.585014ms]
  ✅  Success - Complete job
🏁  Job succeeded
```
(código de salida 0)

### ¿aparece el valor en el log?

`$ act push -s TOKEN=supersecreto123 … | grep -c supersecreto123`

```
0
```
(código de salida 1)

## 3 · Un solo trabajo, una sola combinación

### solo test, solo 3.13

`$ act push -j test --matrix version:3.13 …`

```
✅  Success - Set up job
⭐ Run Main actions/checkout@v4
  ✅  Success - Main actions/checkout@v4 [28.115917ms]
  | probando con la version 3.13
  ✅  Success - Main tests [89.481575ms]
  ✅  Success - Complete job
🏁  Job succeeded
```
(código de salida 0)

## 4 · Una action fijada a un commit completo

### el paso con el SHA

`$ grep uses: .github/workflows/fijado.yml`

```
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
```
(código de salida 0)

### ejecutarlo

`$ act push …`

```
✅  Success - Set up job
⭐ Run Main actions/checkout@11d5960a326750d5838078e36cf38b85af677262
  ✅  Success - Main actions/checkout@11d5960a326750d5838078e36cf38b85af677262 [16.508104ms]
⭐ Run Main ls app.txt && echo "checkout fijado a un commit, ok"
  | checkout fijado a un commit, ok
  ✅  Success - Main ls app.txt && echo "checkout fijado a un commit, ok" [98.657329ms]
  ✅  Success - Complete job
🏁  Job succeeded
```
(código de salida 0)
