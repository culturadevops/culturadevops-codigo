# Salida real — seguridad en el pipeline para PHP

Ejecutado el 2026-10-23T17:56Z en composer:2.

```
### versiones
PHP 8.5.12 (cli) (built: Oct 21 2026 22:49:34) (NTS)
Composer version 2.10.3 2026-08-27 13:34:23
Psalm 6.20.1@376425b8e67b79773add388e16b4f6be5693dc87
PHPStan - PHP Static Analysis Tool 2.3.1

### 1 · psalm normal (sin taint) sobre la app vulnerable
$ vendor/bin/psalm
FILE: src/tienda.php

+----------+------+---------------+-------------------+
| SEVERITY | LINE | ISSUE         | DESCRIPTION       |
+----------+------+---------------+-------------------+
| ERROR    | 20   | ForbiddenCode | Unsafe shell_exec |
+----------+------+---------------+-------------------+

### 2 · psalm --taint-analysis sobre la app vulnerable
$ vendor/bin/psalm --taint-analysis
FILE: src/tienda.php

+----------+------+-----------------------+--------------------------------------------+
| SEVERITY | LINE | ISSUE                 | DESCRIPTION                                |
+----------+------+-----------------------+--------------------------------------------+
| ERROR    | 20   | TaintedShell          | Detected tainted shell code                |
| ERROR    | 27   | TaintedFile           | Detected tainted file handling             |
| ERROR    | 33   | TaintedHtml           | Detected tainted HTML                      |
| ERROR    | 33   | TaintedTextWithQuotes | Detected tainted text with possible quotes |
+----------+------+-----------------------+--------------------------------------------+

### 2b · ¿por qué no salió la inyección SQL? La misma consulta con PDO y con mysqli
$ vendor/bin/psalm --taint-analysis   # en pdo-vs-mysqli/
FILE: src/consultas.php

+----------+------+------------+----------------------+
| SEVERITY | LINE | ISSUE      | DESCRIPTION          |
+----------+------+------------+----------------------+
| ERROR    | 6    | TaintedSql | Detected tainted SQL |
+----------+------+------------+----------------------+

### 3 · phpstan nivel 9 sobre la app vulnerable
$ vendor/bin/phpstan analyse
Note: Using configuration file /demo/app/phpstan.neon.
/demo/app/src/tienda.php:8:Function producto() return type has no value type specified in iterable type array.
/demo/app/src/tienda.php:12:Part $nombre (mixed) of encapsed string cannot be cast to string.
/demo/app/src/tienda.php:20:Binary operation "." between 'ping -c 1 ' and mixed results in an error.
/demo/app/src/tienda.php:27:Binary operation "." between '/srv/facturas/' and mixed results in an error.
/demo/app/src/tienda.php:33:Binary operation "." between '<h1>Hola, ' and mixed results in an error.

### 4 · composer audit
$ composer audit --no-dev --format=summary
Found 14 security vulnerability advisories affecting 1 package.
Run "composer audit" for a full list of advisories.
      1 medium · CVE-2026-69245 · Guzzle: Noncanonical cookie domain keeps subdomain scope
      1 medium · CVE-2026-67355 · Guzzle: Host-only cookie scope is not preserved
      1 medium · CVE-2026-67354 · Guzzle: URI fragments disclosed in redirect Referer headers
      1 medium · CVE-2026-67353 · Guzzle: Unbounded response cookies risk denial of service
      1 medium · CVE-2026-67339 · Guzzle: Proxy-Authorization headers can be sent to origin servers
      1 medium · CVE-2026-59883 · Guzzle: Cookie Disclosure and Injection via IP-Address Domains
      1 medium · CVE-2026-55767 · Dot-only cookie domains match all hosts
      1 medium · CVE-2026-55568 · Silent HTTPS proxy downgrade to cleartext
      1 high · CVE-2026-69246 · Guzzle: Noncanonical host can bypass host-based checks
      1 high · CVE-2022-31091 · Change in port should be considered a change in origin
      1 high · CVE-2022-31090 · CURLOPT_HTTPAUTH option not cleared on change of origin
      1 high · CVE-2022-31043 · Fix failure to strip Authorization header on HTTP downgrade
      1 high · CVE-2022-31042 · Failure to strip the Cookie header on change in host or HTTP downgrade
      1 high · CVE-2022-29248 · Cross-domain cookie leakage

### 4b · ¿y si subo Guzzle a la 7.10.0? Composer ya no me deja
$ composer update   # composer.json: guzzlehttp/guzzle 7.10.0
Loading composer repositories with package information
Updating dependencies
Your requirements could not be resolved to an installable set of packages.
  Problem 1
    - Root composer.json requires guzzlehttp/guzzle 7.10.0 (exact version match: 7.10.0 or 7.10.0.0), found guzzlehttp/guzzle[7.10.0] but these were n
ot loaded, because they are affected by security advisories ("PKSA-gcrk-3vtt-1r14", "PKSA-cnw1-2ytm-cgr8", "PKSA-fy2t-3c5f-827y", "PKSA-qxvb-2bpp-dnk6
", "PKSA-bbs6-q5q9-f3t4", "PKSA-bcdd-5xc7-gwfb", "PKSA-pwsk-hy21-4gby", "PKSA-93qv-9n9h-6k6p", "PKSA-k22t-f949-t9g6"). Go to https://packagist.org/sec
urity-advisories/ to find advisory details. To ignore the advisories, add their IDs to the "policy.advisories.ignore-id" config or add the package to 
"policy.advisories.ignore". To turn the feature off entirely, you can set "policy.advisories.block" to false.

### 4c · lo mismo con el bloqueo desactivado, para poder auditarla
$ composer audit --locked --no-dev --format=summary   # guzzle 7.10.0
Found 9 security vulnerability advisories affecting 1 package.
Run "composer audit" for a full list of advisories.

### 5 · el job del pipeline sobre la app vulnerable
$ ./ci-seguridad.sh app
== psalm --taint-analysis (de dónde viene el dato y adónde llega)
| ERROR    | 20   | TaintedShell          | Detected tainted shell code                |
| ERROR    | 27   | TaintedFile           | Detected tainted file handling             |
| ERROR    | 33   | TaintedHtml           | Detected tainted HTML                      |
| ERROR    | 33   | TaintedTextWithQuotes | Detected tainted text with possible quotes |
== composer audit (dependencias de composer.lock, sin las de desarrollo)
Found 14 security vulnerability advisories affecting 1 package:
PIPELINE: FALLA (hay hallazgos de seguridad)
código de salida: 1

### 6 · el mismo job sobre la app arreglada
$ ./ci-seguridad.sh app-arreglada
== psalm --taint-analysis (de dónde viene el dato y adónde llega)
== composer audit (dependencias de composer.lock, sin las de desarrollo)
No security vulnerability advisories found.
PIPELINE: PASA
código de salida: 0

### 7 · phpstan nivel 9 sobre la app arreglada
Note: Using configuration file /demo/app-arreglada/phpstan.neon.
código de salida: 0
```
