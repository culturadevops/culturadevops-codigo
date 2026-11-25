# SALIDA — 704 · 50 scripts de Bash escritos por IA contra ShellCheck

Generado por `resumen.py` a partir de `resultados.json` (`generar.py` → `analizar.py` → `resumen.py`; `ejecutar_todo.py` lo corre todo).
Fecha de la medición: 2026-10-29. **No es un estudio**: 50 tareas fijas, un modelo local y una muestra de 20 con Claude Code.

## Montaje

- Modelo local: `qwen2.5:7b` por Ollama, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`, /api/chat, opciones temperature=0.2, seed=42, num_ctx=8192, num_predict=2048.
- Claude Code 2.1.312 (`claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --output-format json`), desde un directorio vacío de mktemp, sin herramientas. Modelos que informó: ['claude-haiku-5-5', 'claude-opus-5-5']. Costo total informado (USD): 0.80 (generar 20: 0.53; arreglar 13: 0.27); segundos por script en ronda 0, media: 8.8.
  (`--bare` existe, pero exige ANTHROPIC_API_KEY y la cuenta del dueño es OAuth: `--safe-mode` desactiva CLAUDE.md, hooks, skills y MCP.)
- Muestra de Claude Code: las 20 tareas impares del 1 al 39 (fijada antes de generar).
- ShellCheck 0.11.0 (`koalaman/shellcheck:v0.11.0`, sha256:61862eba…), `-f json1`, todos los niveles. shfmt v3.12.0 (`mvdan/shfmt:v3.12.0`), `-d`.
- Ejecución: contenedor desechable `--rm --network none` (debian:bookworm-20251020-slim + procps, bash 5.2.15). Cada script corre dos veces, cada una en su propio mktemp: **control** (nombres con `_`) y **espacios** (los mismos nombres con espacios). Un check en bash por tarea (tareas.py) dice si la tarea quedó hecha. Timeout 20 s.
- El banco se probó antes con 50 soluciones de referencia escritas a mano (`referencia.py`): 50/50 pasan control y espacios; y con dos scripts sin comillas (fallan solo con espacios, como debe ser).
- Bucle: si la ronda k tiene avisos y k<3, se le da a la misma IA su script y la salida de ShellCheck (formato gcc) y se le pide corregirlo. Un solo turno por llamada. Cuenta como trampa cada `# shellcheck disable` nuevo frente a la ronda 0.
- Criterios fijados antes de mirar: funciona = check OK en control; rompe con espacios = OK en control y falla con espacios; limpio = 0 avisos.

### Prompt (ronda 0)

```
Escribe un script de Bash para esta tarea de administración de sistemas.
Tarea: {tarea}
Uso: {uso}
Solo puedes usar bash y las herramientas de un Debian básico (coreutils, findutils, grep, sed, awk, tar, gzip, procps, util-linux).
Responde solo con el script completo dentro de un bloque ```bash, sin explicaciones.
```

### Prompt (rondas 1-3)

```
Este es tu script:
```bash
{script}
```
ShellCheck 0.11.0 da estos avisos:
{avisos}
Corrige el script para que ShellCheck no dé avisos. Responde solo con el script completo dentro de un bloque ```bash, sin explicaciones.
```

## qwen — 50 scripts

- Ronda 0 con al menos un aviso de ShellCheck: **13 de 50**; avisos en total: 19
- Por nivel: {'info': 11, 'warning': 4, 'error': 1, 'style': 3}
- Por código (avisos · scripts): SC2086 8·5, SC2004 3·2, SC2162 2·2, SC2164 1·1, SC2295 1·1, SC2058 1·1, SC2145 1·1, SC2034 1·1, SC2038 1·1
- SC2086 (variable sin comillas): 8 avisos en 5 scripts
- shfmt -d en ronda 0: {'formato': 49, 'ok': 1}  (ok = ya está en el formato de shfmt)
- Ejecución ronda 0: {'robusto': 27, 'no_funciona': 20, 'rompe_espacios': 3}
- Líneas por script (ronda 0), media: 17.4
- Costumbres (ronda 0): set -euo pipefail en 0; «--» como fin de opciones en 0; -print0 en 6
- Limpios en ronda 0: 37; de ellos robustos al ejecutar: 21
- Ejecución tras el bucle (última ronda): {'robusto': 27, 'no_funciona': 22, 'rompe_espacios': 1}
- ShellCheck limpio en ronda 0 y aun así rompe con espacios: 1 [31]
- ShellCheck limpio en ronda 0 y no hace la tarea ni sin espacios: 15 [5, 8, 10, 13, 15, 16, 21, 23, 24, 26, 27, 30, 43, 47, 49]
- Bucle IA + ShellCheck sobre los 13 con avisos: {'limpio en ronda 1': 8, 'limpio en ronda 2': 1, 'nunca (3 rondas)': 4}
- Supresiones nuevas (# shellcheck disable): ninguna
- Funcionaban y el bucle los rompió: [(37, 'robusto', 'no_funciona')]
- Empeoraron con el bucle (cualquier bajada): [(37, 'robusto', 'no_funciona'), (45, 'rompe_espacios', 'no_funciona')]
- Limpios al final del bucle: 9, de ellos robustos al ejecutar: 5
- No funcionaban bien y el bucle los arregló: [(25, 'rompe_espacios', 'robusto')]

| tarea | avisos r0 | códigos r0 | rondas | avisos final | supr. | r0 control/espacios | final control/espacios | error con espacios (r0) |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 2 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 3 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 4 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 5 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 6 | 1 | 2086 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 7 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 8 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ | mv: cannot move '/tmp/tmp.eqBOVHZKvT/datos de prueba/copia vieja.bak' to '/tmp/tmp.eqbovhz |
| 9 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 10 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ | /s/muestras/qwen/10/r0.sh: line 7: $'TAMA\303\221O=408': command not found /s/muestras/qwe |
| 11 | 1 | 2164 | 2 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 12 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 13 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 14 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 15 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 16 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 17 | 2 | 2058,2295 | 3 | 2 | 0 | ✘/✘ | ✘/✘ | cp: cannot create regular file '/tmp/tmp.nJvBDsH4Rj/destino final/sub carpeta/usuarios.csv |
| 18 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 19 | 2 | 2086,2162 | 1 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 20 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 21 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 22 | 1 | 2145 | 3 | 2 | 0 | ✔/✔ | ✔/✔ |  |
| 23 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ | /s/muestras/qwen/23/r0.sh: line 6: /tmp/tmp.Flu169KQlr/datos de prueba/mi tarea.lock: No s |
| 24 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 25 | 1 | 2086 | 1 | 0 | 0 | ✔/✘ | ✔/✔ | grep: /tmp/tmp.4s9blgYi3t/datos: No such file or directory grep: de: No such file or direc |
| 26 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 27 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 28 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 29 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 30 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 31 | 0 |  | 0 | 0 | 0 | ✔/✘ | ✔/✘ |  |
| 32 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 33 | 1 | 2034 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 34 | 3 | 2086 | 3 | 1 | 0 | ✘/✘ | ✘/✘ | df: /tmp/tmp.dQTEfK1Ot4/datos: No such file or directory df: de: No such file or directory |
| 35 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 36 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 37 | 1 | 2162 | 1 | 0 | 0 | ✔/✔ | ✘/✘ |  |
| 38 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 39 | 2 | 2086 | 1 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 40 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 41 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 42 | 1 | 2004 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 43 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 44 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 45 | 1 | 2038 | 1 | 0 | 0 | ✔/✘ | ✘/✘ | rm: cannot remove '/tmp/tmp.2JXsevJXYp/datos': No such file or directory rm: cannot remove |
| 46 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 47 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 48 | 2 | 2004 | 3 | 1 | 0 | ✘/✘ | ✘/✘ |  |
| 49 | 0 |  | 0 | 0 | 0 | ✘/✘ | ✘/✘ | cp: cannot create regular file '/tmp/tmp.UfOWS8DyDG/destino final//tmp/tmp.UfOWS8DyDG/dato |
| 50 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |

## claude — 20 scripts

- Ronda 0 con al menos un aviso de ShellCheck: **0 de 20**; avisos en total: 0
- Por nivel: {}
- Por código (avisos · scripts): 
- SC2086 (variable sin comillas): 0 avisos en 0 scripts
- shfmt -d en ronda 0: {'formato': 20}  (ok = ya está en el formato de shfmt)
- Ejecución ronda 0: {'robusto': 20}
- Líneas por script (ronda 0), media: 46.1
- Costumbres (ronda 0): set -euo pipefail en 17; «--» como fin de opciones en 12; -print0 en 5
- Limpios en ronda 0: 20; de ellos robustos al ejecutar: 20
- Ejecución tras el bucle (última ronda): {'robusto': 20}
- ShellCheck limpio en ronda 0 y aun así rompe con espacios: 0 []
- ShellCheck limpio en ronda 0 y no hace la tarea ni sin espacios: 0 []

| tarea | avisos r0 | códigos r0 | rondas | avisos final | supr. | r0 control/espacios | final control/espacios | error con espacios (r0) |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 3 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 5 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 7 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 9 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 11 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 13 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 15 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 17 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 19 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 21 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 23 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 25 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 27 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 29 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 31 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 33 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 35 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 37 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 39 | 0 |  | 0 | 0 | 0 | ✔/✔ | ✔/✔ |  |

## Comparación en las MISMAS 20 tareas (impares 1-39)

- qwen: ronda 0 con avisos 7/20 · avisos 10 · ejecución r0 {'robusto': 9, 'no_funciona': 9, 'rompe_espacios': 2}
- claude: ronda 0 con avisos 0/20 · avisos 0 · ejecución r0 {'robusto': 20}

## Bucle cruzado: los MISMOS scripts de qwen con avisos, arreglados por cada IA

`python generar.py cruzado`: la ronda 0 es la de qwen copiada tal cual; las rondas 1-3 las hace Claude Code con el mismo PROMPT_ARREGLO.

## cruzado (arregla Claude Code) — 13 scripts

- Ronda 0 con al menos un aviso de ShellCheck: **13 de 13**; avisos en total: 19
- Por nivel: {'info': 11, 'warning': 4, 'error': 1, 'style': 3}
- Por código (avisos · scripts): SC2086 8·5, SC2004 3·2, SC2162 2·2, SC2164 1·1, SC2295 1·1, SC2058 1·1, SC2145 1·1, SC2034 1·1, SC2038 1·1
- SC2086 (variable sin comillas): 8 avisos en 5 scripts
- shfmt -d en ronda 0: {'formato': 13}  (ok = ya está en el formato de shfmt)
- Ejecución ronda 0: {'robusto': 6, 'no_funciona': 5, 'rompe_espacios': 2}
- Líneas por script (ronda 0), media: 19.5
- Costumbres (ronda 0): set -euo pipefail en 0; «--» como fin de opciones en 0; -print0 en 4
- Limpios en ronda 0: 0; de ellos robustos al ejecutar: 0
- Ejecución tras el bucle (última ronda): {'robusto': 10, 'no_funciona': 3}
- ShellCheck limpio en ronda 0 y aun así rompe con espacios: 0 []
- ShellCheck limpio en ronda 0 y no hace la tarea ni sin espacios: 0 []
- Bucle IA + ShellCheck sobre los 13 con avisos: {'limpio en ronda 1': 13}
- Supresiones nuevas (# shellcheck disable): ninguna
- Funcionaban y el bucle los rompió: ninguno
- Empeoraron con el bucle (cualquier bajada): ninguno
- Limpios al final del bucle: 13, de ellos robustos al ejecutar: 10
- No funcionaban bien y el bucle los arregló: [(17, 'no_funciona', 'robusto'), (25, 'rompe_espacios', 'robusto'), (34, 'no_funciona', 'robusto'), (45, 'rompe_espacios', 'robusto')]

| tarea | avisos r0 | códigos r0 | rondas | avisos final | supr. | r0 control/espacios | final control/espacios | error con espacios (r0) |
|---|---|---|---|---|---|---|---|---|
| 6 | 1 | 2086 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 11 | 1 | 2164 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 17 | 2 | 2058,2295 | 1 | 0 | 0 | ✘/✘ | ✔/✔ | cp: cannot create regular file '/tmp/tmp.S1IUTN5KGK/destino final/sub carpeta/usuarios.csv |
| 19 | 2 | 2086,2162 | 1 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 22 | 1 | 2145 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 25 | 1 | 2086 | 1 | 0 | 0 | ✔/✘ | ✔/✔ | grep: /tmp/tmp.bMjMPvdTY8/datos: No such file or directory grep: de: No such file or direc |
| 33 | 1 | 2034 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 34 | 3 | 2086 | 1 | 0 | 0 | ✘/✘ | ✔/✔ | df: /tmp/tmp.WdhwUcsy7I/datos: No such file or directory df: de: No such file or directory |
| 37 | 1 | 2162 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 39 | 2 | 2086 | 1 | 0 | 0 | ✘/✘ | ✘/✘ |  |
| 42 | 1 | 2004 | 1 | 0 | 0 | ✔/✔ | ✔/✔ |  |
| 45 | 1 | 2038 | 1 | 0 | 0 | ✔/✘ | ✔/✔ | rm: cannot remove '/tmp/tmp.cfT7Fq5tS5/datos': No such file or directory rm: cannot remove |
| 48 | 2 | 2004 | 1 | 0 | 0 | ✘/✘ | ✘/✘ |  |

## Ejemplos que salen en pantalla (ejecutados por ejemplos.py)

- Banco: 50 /50 referencias OK (control y espacios)
- neg 1: control OK · espacios: cp: cannot stat '/tmp/tmp.AqK0XvsmF8/datos': No such file or directory cp: cannot stat 'de': No such file or d
- neg 6: control OK · espacios: find: '/tmp/tmp.fLam76ySXO/datos': No such file or directory find: 'de': No such file or directory find: 'prue

### shellcheck -f gcc · qwen tarea 34, ronda 0
```
r0.sh:6:13: note: Double quote to prevent globbing and word splitting. [SC2086]
r0.sh:8:6: note: Double quote to prevent globbing and word splitting. [SC2086]
r0.sh:8:15: note: Double quote to prevent globbing and word splitting. [SC2086]
Unable to find image 'koalaman/shellcheck:v0.11.0' locally
v0.11.0: Pulling from koalaman/shellcheck
08ea58bc53cf: Pulling fs layer
957cfdbf2dcf: Pulling fs layer
85c0474c1024: Download complete
957cfdbf2dcf: Download complete
957cfdbf2dcf: Pull complete
08ea58bc53cf: Download complete
08ea58bc53cf: Pull complete
Digest: sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d
Status: Downloaded newer image for koalaman/shellcheck:v0.11.0
```

### shfmt -d · Claude tarea 1 (primeras líneas)
```
diff r0.sh.orig r0.sh
--- r0.sh.orig
+++ r0.sh
@@ -2,8 +2,8 @@
 set -euo pipefail
 
 if [ "$#" -ne 2 ]; then
-    echo "Uso: $0 DIR DEST" >&2
-    exit 1
+	echo "Uso: $0 DIR DEST" >&2
```

### qwen tarea 31 con espacios (ShellCheck: 0 avisos)
```
8.0K /tmp/tmp.ZgWfrS8UNY/datos
```
