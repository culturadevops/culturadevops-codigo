# SALIDA — Un escáner de seguridad para cada lenguaje (cultura-devops)

Generado 2026-10-23 18:14 UTC con `python correr.py`. Código vulnerable A PROPÓSITO (app/, ver LEEME.md): nunca se despliega.

Verdad de referencia en cada lenguaje: V1 inyección SQL · V2 inyección de comandos · V3 inyección SQL armada en otro archivo · S1 consulta con parámetros (segura) · S2 id convertido a entero (seguro). ✔/✘ = detectó o no V1, V2, V3.

## PHP · Psalm (taint analysis) + composer audit

### versión

`$ psalm --version`

```
Psalm 6.20.1@376425b8e67b79773add388e16b4f6be5693dc87
```
(código de salida 0)

### Psalm --taint-analysis

`$ psalm --taint-analysis`

```
php/index.php:15  TaintedShell  Detected tainted shell code
```
(código de salida 2 · 0.8 s de análisis)

**Puntuación** (Psalm, php): ✘✔✘ · aciertos 1/3 · falsos positivos: — · otros avisos: 0

### la sonda

`$ cat sonda.php`

```
<?php
$db = new PDO("sqlite:x");
$db->query("SELECT " . $_GET["a"]);
$m = new mysqli();
$m->query("SELECT " . $_GET["b"]);
mysqli_query($m, "SELECT " . $_GET["c"]);
```
(código de salida 0)

### Psalm sobre la sonda: PDO contra mysqli

`$ psalm --taint-analysis sonda.php`

```
| ERROR    | 5    | TaintedSql | Detected tainted SQL |
| ERROR    | 6    | TaintedSql | Detected tainted SQL |
```
(código de salida 0)

> Misma consulta, mismo dato del usuario: con mysqli (líneas 5 y 6) sale TaintedSql; con PDO (línea 3), nada.

### Composer se niega a instalar la versión vieja

`$ composer update`

```
Problem 1
    - Root composer.json requires guzzlehttp/guzzle 7.4.0 (exact version match: 7.4.0 or 7.4.0.0), found guzzlehttp/guzzle[7.4.0] but these were not loaded, because they are affected by security advisories (…14 avisos…). Go to https://packagist.org/security-ad
```
(código de salida 2)

> Composer 2.10.3 bloquea por defecto instalar una versión con avisos de seguridad publicados (policy.advisories.block).

### composer audit (con el bloqueo desactivado, solo en esta copia)

`$ composer audit --locked`

```
14 avisos en guzzlehttp/guzzle 7.4.0 · por gravedad: {'high': 6, 'medium': 8}
  CVE-2026-69246  high  Guzzle: Noncanonical host can bypass host-based checks
  CVE-2026-69245  medium  Guzzle: Noncanonical cookie domain keeps subdomain scope
  CVE-2026-67354  medium  Guzzle: URI fragments disclosed in redirect Referer headers
  CVE-2026-67355  medium  Guzzle: Host-only cookie scope is not preserved
  CVE-2026-67353  medium  Guzzle: Unbounded response cookies risk denial of service
  …
```
(código de salida 0 · 2.2 s de análisis)

## Python · Bandit + pip-audit

### versiones

`$ bandit --version; pip-audit --version`

```
bandit 1.9.4
pip-audit 2.10.1
```
(código de salida 0)

### Bandit

`$ bandit -r python`

```
python/app.py:3  B404  Consider possible security implications associated with the subprocess module.
python/app.py:20  B608  Possible SQL injection vector through string-based query construction.
python/app.py:27  B602  subprocess call with shell=True identified, security issue.
python/app.py:46  B608  Possible SQL injection vector through string-based query construction.
python/consultas.py:6  B608  Possible SQL injection vector through string-based query construction.
```
(código de salida 1 · 0.2 s de análisis)

**Puntuación** (Bandit, python): ✔✔✔ · aciertos 3/3 · falsos positivos: S2 · otros avisos: 1

### pip-audit

`$ pip-audit -r requirements.txt`

```
flask 2.2.2: 4 vulnerabilidades
requests 2.25.1: 8 vulnerabilidades
idna 2.10: 4 vulnerabilidades
urllib3 1.26.20: 12 vulnerabilidades
TOTAL: 28
```
(código de salida 1 · 3.3 s de análisis)

> requests 2.25.1 trae dependencias viejas (idna, urllib3): pip-audit las revisa también.

## Go · gosec + govulncheck

### versiones

`$ go version; govulncheck -version`

```
go version go1.27.2 linux/amd64
Go: go1.27.2
Scanner: govulncheck@v1.9.0
DB: https://vuln.go.dev
```
(código de salida 0)

### gosec

`$ gosec ./...`

```
go/consultas.go:8  G202  SQL string concatenation
go/consultas.go:9  G701  SQL injection via taint analysis: (*database/sql.DB).Query
go/main.go:19  G701  SQL injection via taint analysis: (*database/sql.DB).Query
go/main.go:19  G202  SQL string concatenation
go/main.go:20  G705  XSS via taint analysis: fmt.Fprint
go/main.go:26  G702  Command injection via taint analysis: os/exec.Command
go/main.go:26  G204  Subprocess launched with a potential tainted input or cmd arguments
go/main.go:27  G705  XSS via taint analysis: (net/http.ResponseWriter).Write
go/main.go:27  G104  Errors unhandled
go/main.go:32  G705  XSS via taint analysis: fmt.Fprint
go/main.go:38  G705  XSS via taint analysis: fmt.Fprint
go/main.go:48  G701  SQL injection via taint analysis: (*database/sql.DB).Query
go/main.go:48  G202  SQL string concatenation
go/main.go:55  G705  XSS via taint analysis: fmt.Fprint
go/main.go:66  G114  Use of net/http serve function that has no support for setting timeouts
go/main.go:66  G104  Errors unhandled
```
(código de salida 1 · 0.5 s de análisis)

**Puntuación** (gosec, go): ✔✔✔ · aciertos 3/3 · falsos positivos: S2 · otros avisos: 8

### gosec en una copia SIN go.sum

`$ rm go.sum && gosec ./...`

```
Golang errors in file: [/sin-sum/main.go]:
  Issues : 7
```
(código de salida 0)

> Sin go.sum, gosec no puede cargar los tipos: avisa de «Golang errors» y se salta el análisis de taint (G701/G702): 7 hallazgos en vez de 16. El trabajo de act sigue en rojo, pero con menos de la mitad.

### govulncheck

`$ govulncheck ./...`

```
=== Symbol Results ===

Vulnerability #1: GO-2021-0113
    Out-of-bounds read in golang.org/x/text/language
  More info: https://pkg.go.dev/vuln/GO-2021-0113
  Module: golang.org/x/text
    Found in: golang.org/x/text@v0.3.5
    Fixed in: golang.org/x/text@v0.3.7
    Example traces found:
      #1: main.go:54:31: tienda.idioma calls language.Parse

Your code is affected by 1 vulnerability from 1 module.
This scan also found 2 vulnerabilities in packages you import and 2
vulnerabilities in modules you require, but your code doesn't appear to call
these vulnerabilities.
Use '-show verbose' for more details.
```
(código de salida 3 · 2.5 s de análisis)

> govulncheck no solo dice «tienes una versión vieja»: dice si tu código LLAMA a la función vulnerable.

## Java · SpotBugs + Find Security Bugs, y Trivy para las dependencias

### versión

`$ mvn -v`

```
Apache Maven 3.9.16 (2bdd9fddda4b155ebf8000e807eb73fd829a51d5)
```
(código de salida 0)

### SpotBugs + Find Security Bugs

`$ mvn spotbugs:spotbugs`

```
java/Consultas.java:16  EXPERIMENTAL  OBL_UNSATISFIED_OBLIGATION_EXCEPTION_EDGE
java/Consultas.java:16  SECURITY  SQL_INJECTION_JDBC
java/Consultas.java:16  SECURITY  SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE
java/TiendaServlet.java:13  BAD_PRACTICE  SE_NO_SERIALVERSIONID
java/TiendaServlet.java:25  SECURITY  SERVLET_PARAMETER
java/TiendaServlet.java:26  EXPERIMENTAL  OBL_UNSATISFIED_OBLIGATION
java/TiendaServlet.java:26  EXPERIMENTAL  OBL_UNSATISFIED_OBLIGATION
java/TiendaServlet.java:26  BAD_PRACTICE  ODR_OPEN_DATABASE_RESOURCE
java/TiendaServlet.java:26  CORRECTNESS  RV_RETURN_VALUE_IGNORED
java/TiendaServlet.java:26  SECURITY  SQL_INJECTION_JDBC
java/TiendaServlet.java:26  SECURITY  SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE
java/TiendaServlet.java:30  SECURITY  SERVLET_PARAMETER
java/TiendaServlet.java:31  SECURITY  COMMAND_INJECTION
java/TiendaServlet.java:35  SECURITY  SERVLET_PARAMETER
java/TiendaServlet.java:38  BAD_PRACTICE  ODR_OPEN_DATABASE_RESOURCE
java/TiendaServlet.java:39  SECURITY  SERVLET_PARAMETER
java/TiendaServlet.java:40  CORRECTNESS  RV_RETURN_VALUE_IGNORED
java/TiendaServlet.java:44  SECURITY  SERVLET_PARAMETER
java/TiendaServlet.java:45  SECURITY  SQL_INJECTION_JDBC
```
(código de salida 0 · 4.6 s de análisis)

**Puntuación** (SpotBugs+FSB, java): ✔✔✔ · aciertos 3/3 · falsos positivos: S2 · otros avisos: 13

### Trivy sobre el pom.xml

`$ trivy fs --scanners vuln --offline-scan java`

```
Total: 7 (UNKNOWN: 0, LOW: 0, MEDIUM: 4, HIGH: 1, CRITICAL: 2)
│ org.apache.logging.log4j:log4j-core │ CVE-2021-44228 │ CRITICAL │ fixed  │ 2.14.1            │ 2.15.0, 2.3.1, 2.12.2 │ log4j-core: Remote code execution in Log4j 2.x when logs    │
│                                     │ CVE-2021-45046 │          │        │                   │ 2.16.0, 2.12.2, 2.3.1 │ log4j-core: DoS in log4j 2.x with thread context message    │
│                                     │ CVE-2021-45105 │ HIGH     │        │                   │ 2.12.3, 2.17.0, 2.3.1 │ log4j-core: DoS in log4j 2.x with Thread Context Map (MDC)  │
│                                     │ CVE-2021-44832 │ MEDIUM   │        │                   │ 2.3.2, 2.12.4, 2.17.1 │ log4j-core: remote code execution via JDBC Appender         │
│                                     │ CVE-2026-34477 │          │        │                   │ 2.25.4                │ org.apache.logging.log4j/log4j-core: Apache Log4j Core:     │
```
(código de salida 0 · 0.2 s de análisis)

> OWASP Dependency-Check es la opción clásica para Java, pero la primera vez descarga la base completa de la NVD (sin clave de API, horas). Trivy hace el mismo trabajo sobre el pom.xml en segundos; es lo que se usa aquí. --offline-scan: sin preguntar a Maven Central, que el día de la demo respondió 429 (demasiadas peticiones); así ve las dependencias directas del pom, no las transitivas (log4j-api).

## Node · njsscan + npm audit

### njsscan

`$ njsscan node`

```
node/app.js:18  generic_os_command_exec
```
(código de salida 1 · 2.7 s de análisis)

**Puntuación** (njsscan, node): ✘✔✘ · aciertos 1/3 · falsos positivos: — · otros avisos: 0

### npm audit

`$ npm audit`

```
vulnerabilidades por gravedad: {'info': 0, 'low': 5, 'moderate': 0, 'high': 9, 'critical': 1, 'total': 15}
paquetes afectados: @tootallnate/once, body-parser, cacache, cookie, express, http-proxy-agent, lodash, make-fetch-happen, node-gyp, path-to-regexp, qs, send, serve-static, sqlite3, tar
```
(código de salida 1 · 1.2 s de análisis)

## Resumen

| Lenguaje | Herramienta | V1 V2 V3 | Falsos positivos | Otros avisos | Segundos |
|---|---|---|---|---|---|
| php | Psalm | ✘✔✘ | — | 0 | 0.8 |
| python | Bandit | ✔✔✔ | S2 | 1 | 0.2 |
| go | gosec | ✔✔✔ | S2 | 8 | 0.5 |
| java | SpotBugs+FSB | ✔✔✔ | S2 | 13 | 4.6 |
| node | njsscan | ✘✔✘ | — | 0 | 2.7 |

## Todo junto: el workflow de GitHub Actions, ejecutado en local con act

### el workflow

`$ cat .github/workflows/seguridad.yml`

```
# Un escáner de seguridad por lenguaje: el código (SAST) y las dependencias (SCA).
# Cada trabajo falla si encuentra algo: así el pipeline se pone en rojo antes de desplegar.
name: seguridad
on: [push, pull_request]

jobs:
  php:
    runs-on: ubuntu-latest
    container: composer:2.10.3
    steps:
      - uses: actions/checkout@v4
      - name: psalm (taint analysis)
        working-directory: php
        run: |
          composer global require -q vimeo/psalm:6.20.1
          composer dump-autoload -q
          PSALM="$(composer global config bin-dir --absolute -q)/psalm"
          $PSALM --init . 1 >/dev/null
          $PSALM --taint-analysis --no-cache --no-progress
      - name: composer (bloquea versiones con avisos de seguridad)
        working-directory: php
        run: composer update --no-install --no-interaction && composer audit --locked

  python:
    runs-on: ubuntu-latest
    container: python:3.13-slim
    steps:
      - uses: actions/checkout@v4
      - name: bandit
        run: pip install -q bandit==1.9.4 && bandit -r python -q
      - name: pip-audit
        run: pip install -q pip-audit==2.10.1 && pip-audit -r python/requirements.txt

  go:
    runs-on: ubuntu-latest
    container: golang:1.27.2
    steps:
      - uses: actions/checkout@v4
      - name: gosec
        working-directory: go
        run: go run github.com/securego/gosec/v2/cmd/gosec@v2.30.0 -quiet ./...
      - name: govulncheck
        working-directory: go
        run: go run golang.org/x/vuln/cmd/govulncheck@v1.9.0 ./...

  java:
    runs-on: ubuntu-latest
    container: maven:3.9.16-eclipse-temurin-21
    steps:
      - uses: actions/checkout@v4
      - name: spotbugs + find security bugs
        working-directory: java
        run: mvn -q -B compile com.github.spotbugs:spotbugs-maven-plugin:4.9.3.0:check

  java-dependencias:
    runs-on: ubuntu-latest
    container: aquasec/trivy:0.75.0
    steps:
      - uses: actions/checkout@v4
      - name: trivy (dependencias del pom)
        run: trivy fs --scanners vuln --offline-scan --exit-code 1 --severity HIGH,CRITICAL --quiet java

  node:
    runs-on: ubuntu-latest
    container: node:22-bookworm-slim
    steps:
      - uses: actions/checkout@v4
      - name: npm audit
        working-directory: node
        run: npm install --package-lock-only --ignore-scripts --no-audit -q && npm audit --audit-level=high

  node-codigo:
    runs-on: ubuntu-latest
    container: python:3.13-slim
    steps:
      - uses: actions/checkout@v4
      - name: njsscan
        run: pip install -q njsscan==1.0.1 && njsscan node
```
(código de salida 0)

### los trabajos

`$ act -l`

```
Stage  Job ID             Job name           Workflow name  Workflow file  Events           
0      node-codigo        node-codigo        seguridad      seguridad.yml  push,pull_request
0      php                php                seguridad      seguridad.yml  push,pull_request
0      python             python             seguridad      seguridad.yml  push,pull_request
0      go                 go                 seguridad      seguridad.yml  push,pull_request
0      java               java               seguridad      seguridad.yml  push,pull_request
0      java-dependencias  java-dependencias  seguridad      seguridad.yml  push,pull_request
0      node               node               seguridad      seguridad.yml  push,pull_request
time="2026-10-23T18:16:49Z" level=info msg="Using docker host 'unix:///var/run/docker.sock', and daemon socket 'unix:///var/run/docker.sock'"
```
(código de salida 0)

### act push

`$ act push`

```
[seguridad/go               ]   ❌  Failure - Main gosec
[seguridad/java             ]   ❌  Failure - Main spotbugs + find security bugs
[seguridad/java-dependencias]   ❌  Failure - Main trivy (dependencias del pom)
[seguridad/node             ]   ❌  Failure - Main npm audit
[seguridad/node-codigo      ]   ❌  Failure - Main njsscan
[seguridad/php              ]   ❌  Failure - Main psalm (taint analysis)
[seguridad/python           ]   ❌  Failure - Main bandit
```
(código de salida 0 · 48.5 s de análisis)

> Cada trabajo es independiente: todos corren, y el pipeline queda en rojo si alguno encuentra algo.

### por qué falló cada trabajo (contado en el registro de act)

`$ grep … act.log`

```
php                1 errors found (Psalm)
python             5 hallazgos (Bandit)
go                 Issues : 16 (gosec)
java               19 hallazgos (spotbugs:check)
java-dependencias  Total: 3 (HIGH: 1, CRITICAL: 2) (Trivy)
node               15 vulnerabilities (5 low, 9 high, 1 critical) (npm audit)
node-codigo        1 regla(s) disparada(s) (njsscan)
```
(código de salida 0)
