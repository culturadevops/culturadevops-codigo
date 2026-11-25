# SALIDA — Semgrep vs CodeQL vs SonarQube (cultura-devops)

Generado 2026-10-23 18:08 UTC con `python correr.py`. Código vulnerable A PROPÓSITO (../demo-sast-por-lenguaje/app): nunca se despliega.

En cada lenguaje: V1 inyección SQL · V2 inyección de comandos · V3 inyección SQL armada en otro archivo (aciertos) · S1 consulta con parámetros · S2 id convertido a entero (seguros: si se marcan, son falsos positivos).

## Semgrep CE

### Semgrep 1.181.1 · p/default

`$ semgrep scan --config p/default .`

```
.github/workflows/seguridad.yml:11  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:28  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:38  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:50  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:59  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:67  github-actions-mutable-action-tag
.github/workflows/seguridad.yml:76  github-actions-mutable-action-tag
go/consultas.go:8  string-formatted-query
go/consultas.go:9  gosql-sqli
go/main.go:19  string-formatted-query
go/main.go:19  tainted-sql-string
go/main.go:20  no-fprintf-to-responsewriter
go/main.go:26  dangerous-exec-command
go/main.go:27  no-direct-write-to-responsewriter
go/main.go:32  no-fprintf-to-responsewriter
go/main.go:38  no-fprintf-to-responsewriter
go/main.go:48  string-formatted-query
go/main.go:49  no-fprintf-to-responsewriter
go/main.go:55  no-fprintf-to-responsewriter
go/main.go:66  use-tls
java/src/main/java/tienda/Consultas.java:16  formatted-sql-string
node/app.js:7  express-check-csurf-middleware-usage
node/app.js:19  detect-child-process
php/index.php:11  tainted-sql-string
php/index.php:15  exec-use
php/index.php:15  tainted-exec
php/index.php:15  tainted-exec
php/index.php:27  tainted-sql-string
python/app.py:19  sql-injection-db-cursor-execute
python/app.py:20  sqlalchemy-execute-raw-query
python/app.py:20  tainted-sql-string
python/app.py:20  tainted-sql-string
python/app.py:27  subprocess-injection
python/app.py:27  dangerous-subprocess-use
python/app.py:27  subprocess-shell-true
python/app.py:46  sqlalchemy-execute-raw-query
python/app.py:46  tainted-sql-string
python/app.py:46  tainted-sql-string
python/consultas.py:7  sqlalchemy-execute-raw-query
```
(código de salida 0 · 5.3 s)

> El tiempo incluye bajar las reglas del registro de Semgrep (no hace falta cuenta).

## CodeQL

### versión y lenguajes que entiende

`$ codeql version; codeql resolve languages`

```
CodeQL command-line toolchain release 2.27.3.
actions cpp csharp csv go html java javascript properties python ruby rust swift xml yaml
```
(código de salida 0)

> No hay «php» en la lista: CodeQL no analiza PHP.

### CodeQL · python

`$ codeql database create … && codeql database analyze … codeql/python-queries`

```
python/app.py:20  py/sql-injection
python/app.py:27  py/command-line-injection
python/consultas.py:7  py/sql-injection
```
(código de salida 0 · 10.7 s)

### CodeQL · javascript

`$ codeql database create … && codeql database analyze … codeql/javascript-queries`

```
node/app.js:10  js/missing-rate-limiting
node/app.js:13  js/sql-injection
node/app.js:16  js/missing-rate-limiting
node/app.js:19  js/command-line-injection
node/app.js:27  js/missing-rate-limiting
node/app.js:32  js/missing-rate-limiting
node/consultas.js:6  js/sql-injection
```
(código de salida 0 · 20.0 s)

### CodeQL · go

`$ codeql database create … && codeql database analyze … codeql/go-queries`

```
go/consultas.go:9  go/sql-injection
go/main.go:19  go/sql-injection
go/main.go:26  go/command-injection
```
(código de salida 0 · 14.4 s)

### CodeQL · java

`$ codeql database create … && codeql database analyze … codeql/java-queries`

```
java/src/main/java/tienda/Consultas.java:16  java/sql-injection
java/src/main/java/tienda/TiendaServlet.java:26  java/sql-injection
java/src/main/java/tienda/TiendaServlet.java:31  java/command-line-injection
```
(código de salida 0 · 24.9 s)

## SonarQube Community Build

### el servidor

`$ docker run sonarqube:community`

```
SonarQube 26.10.0.133078 · UP en 36 s
```
(código de salida 0)

> SonarQube necesita un servidor (con su base de datos y su Elasticsearch) antes de analizar nada.

### sonar-scanner

`$ sonar-scanner -Dsonar.projectKey=tienda-vulnerable …`

```
18:11:05.006 INFO  QUALITY GATE STATUS: PASSED - View details on http://localhost:9000/dashboard?id=tienda-vulnerable
18:11:05.113 INFO  EXECUTION SUCCESS
```
(código de salida 0 · 19.4 s)

### lo que marca como seguridad

`$ GET /api/issues/search?impactSoftwareQualities=SECURITY (+ /api/hotspots/search)`

```
java/src/main/java/tienda/Consultas.java:16  java:S2077  Make sure using a dynamically formatted SQL query is safe here.
java/src/main/java/tienda/TiendaServlet.java:26  java:S2077  Make sure using a dynamically formatted SQL query is safe here.
java/src/main/java/tienda/TiendaServlet.java:31  java:S4036  Make sure the "PATH" variable only contains fixed, unwriteable directories.
java/src/main/java/tienda/TiendaServlet.java:45  java:S2077  Make sure using a dynamically formatted SQL query is safe here.
node/app.js:7  javascript:S5689  This framework implicitly discloses version information by default. Make sure it
php/index.php:11  php:S2077  Make sure that formatting this SQL query is safe here.
php/index.php:27  php:S2077  Make sure that formatting this SQL query is safe here.
python/app.py:9  python:S4502  Make sure disabling CSRF protection is safe here.

(issues de todo tipo en el proyecto: 10)
```
(código de salida 0)

> En la Community Build no hay análisis de taint: lo de seguridad son reglas que piden revisar la línea.

## Resumen por lenguaje

| Herramienta | Lenguaje | V1 V2 V3 | Falsos positivos | Otros avisos |
|---|---|---|---|---|
| Semgrep | php | ✔✔✘ | S2 | 0 |
| Semgrep | python | ✔✔✔ | S2 | 0 |
| Semgrep | go | ✔✔✔ | S2 | 6 |
| Semgrep | java | ✘✘✔ | — | 0 |
| Semgrep | node | ✘✔✘ | — | 1 |
| CodeQL | php | no lo soporta | — | — |
| CodeQL | python | ✔✔✔ | — | 0 |
| CodeQL | go | ✔✔✔ | — | 0 |
| CodeQL | java | ✔✔✔ | — | 0 |
| CodeQL | node | ✔✔✔ | — | 4 |
| SonarQube CB | php | ✔✘✘ | S2 | 0 |
| SonarQube CB | python | ✘✘✘ | — | 1 |
| SonarQube CB | go | ✘✘✘ | — | 0 |
| SonarQube CB | java | ✔✔✔ | S2 | 0 |
| SonarQube CB | node | ✘✘✘ | — | 1 |

## Resumen total

| Herramienta | Aciertos | Falsos positivos | Otros avisos | Segundos |
|---|---|---|---|---|
| Semgrep | 10/15 | 3 | 7 | 5 |
| CodeQL | 12/12 | 0 | 4 | 70 |
| SonarQube CB | 4/15 | 2 | 2 | 19 |
