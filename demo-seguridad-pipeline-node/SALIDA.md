# Salida real — seguridad en el pipeline para Node.js

Ejecutado el 2026-10-23T17:49Z.

```
### versiones (njsscan)
njsscan: v1.0.1 | Ajin Abraham | opensecurity.in[0m

### 1 · njsscan sobre la app vulnerable
$ njsscan app/
│ RULE ID     │ node_api_key                                                                              │
│ DESCRIPTION │ A hardcoded API Key is identified. Store it properly in an environment variable.          │
│ SEVERITY    │ ERROR                                                                                     │
│ FILES       │ ╒════════════════╤══════════════════════════════════════════
│             │ │ File           │ app/server.js                                                        │ │
╘═════════════╧═══════════════════════════════════════════════════�
│ RULE ID     │ generic_os_command_exec                                                                            │
│ DESCRIPTION │ User controlled data in 'child_process.exec()' can result in Remote OS Command Execution.          │
│ SEVERITY    │ ERROR                                                                                              │
│ FILES       │ ╒════════════════╤══════════════════════════════════════════
│             │ │ File           │ app/server.js                                                           │       │
╘═════════════╧═══════════════════════════════════════════════════�
│ RULE ID     │ express_xss                                                                                            │
│ DESCRIPTION │ Untrusted User Input in Response will result in Reflected Cross Site Scripting Vulnerability.          │
│ SEVERITY    │ ERROR                                                                                                  │
│ FILES       │ ╒════════════════╤══════════════════════════════════════════
│             │ │ File           │ app/server.js                                                                     │ │
╘═════════════╧═══════════════════════════════════════════════════�
│ RULE ID     │ generic_path_traversal                                                                                                                                                              
│ DESCRIPTION │ Untrusted user input in createReadStream()/readFile()/readFileSync()/readFileAsync() can end up in Directory Traversal Attack. A Directory Traversal Attack (also known as Path Trav
│ SEVERITY    │ ERROR                                                                                                                                                                               
│ FILES       │ ╒════════════════╤══════════════════════════════════════════
│             │ │ File           │ app/server.js                                                                     │                                                                        
╘═════════════╧═══════════════════════════════════════════════════�
│ RULE ID     │ join_resolve_path_traversal                                                                                                   │
│ DESCRIPTION │ Path constructed with user input can result in Path Traversal. Ensure that user input does not reach `join()` or `resolve()`. │
│ SEVERITY    │ WARNING                                                                                                                       │
│ FILES       │ ╒════════════════╤══════════════════════════════════════════
│             │ │ File           │ app/server.js                                                                     │                        │
╘═════════════╧═══════════════════════════════════════════════════�
código de salida: 1

### 1b · njsscan, solo los identificadores de regla
express_xss · ERROR · 26
generic_os_command_exec · ERROR · 21
generic_path_traversal · ERROR · 26
join_resolve_path_traversal · WARNING · 26
node_api_key · ERROR · 12

### 1c · ¿por qué no salió la inyección SQL? La misma consulta con mysql y con mysql2
require('mysql'): node_sqli_injection
require('mysql2'): sin node_sqli_injection

### 2 · njsscan sobre la app arreglada, SIN las anotaciones njsscan-ignore
3 hallazgos
express_xss · ERROR · línea 29
generic_path_traversal · ERROR · línea 29
join_resolve_path_traversal · WARNING · línea 29
código de salida: 1

### 2b · njsscan sobre la app arreglada, CON las anotaciones (falsos positivos revisados)
29:  const ruta = path.resolve(FACTURAS, path.basename(String(req.query.archivo))); // njsscan-ignore: join_resolve_path_traversal
31:  res.send(fs.readFileSync(ruta, 'utf8')); // njsscan-ignore: generic_path_traversal, express_xss
0 hallazgos
código de salida: 0

### versiones (node)
v22.23.2
npm 10.9.8
v10.13.0
`-- eslint-plugin-security@4.2.0

### 3 · eslint-plugin-security sobre la app vulnerable
$ npx eslint .

/demo/app/server.js
  21:3   warning  Found child_process.exec() with non Literal first argument                 security/detect-child-process
  26:12  warning  Found readFileSync from package "fs" with non literal argument at index 0  security/detect-non-literal-fs-filename

✖ 2 problems (0 errors, 2 warnings)

código de salida: 0
$ npx eslint . --max-warnings 0
código de salida: 1

### 4 · npm audit sobre la app vulnerable (solo lo que se despliega)
$ npm audit --omit=dev
# npm audit report

body-parser  <=1.20.5
Severity: high
body-parser vulnerable to denial of service when url encoding is enabled - https://github.com/advisories/GHSA-qwcr-r2fm-qrc7
body-parser vulnerable to denial of service when invalid limit value silently disables size enforcement - https://github.com/advisories/GHSA-v422-hmwv-36x6
Depends on vulnerable versions of qs
fix available via `npm audit fix --force`
Will install express@4.22.3, which is outside the stated dependency range
node_modules/body-parser
  express  <=4.21.2 || 5.0.0-alpha.1 - 5.0.0
  Depends on vulnerable versions of body-parser
  Depends on vulnerable versions of cookie
  Depends on vulnerable versions of path-to-regexp
  Depends on vulnerable versions of qs
  Depends on vulnerable versions of send
  Depends on vulnerable versions of serve-static
  node_modules/express

cookie  <0.7.0
cookie accepts cookie name, path, and domain with out of bounds characters - https://github.com/advisories/GHSA-pxg6-pf52-xh8x
fix available via `npm audit fix --force`
Will install express@4.22.3, which is outside the stated dependency range
node_modules/cookie


lodash  <=4.17.23
Severity: high
Command Injection in lodash - https://github.com/advisories/GHSA-35jh-r3h4-6jhm
Regular Expression Denial of Service (ReDoS) in lodash - https://github.com/advisories/GHSA-29mw-wpgm-hmr9
lodash vulnerable to Code Injection via `_.template` imports key names - https://github.com/advisories/GHSA-r5fr-rjxr-66jc
lodash vulnerable to Prototype Pollution via array path bypass in `_.unset` and `_.omit` - https://github.com/advisories/GHSA-f23m-r3pf-42rh
Lodash has Prototype Pollution Vulnerability in `_.unset` and `_.omit` functions - https://github.com/advisories/GHSA-xxjr-mmjv-4gpg
fix available via `npm audit fix --force`
Will install lodash@4.18.1, which is outside the stated dependency range
node_modules/lodash

path-to-regexp  <=0.1.12
Severity: high
path-to-regexp outputs backtracking regular expressions - https://github.com/advisories/GHSA-9wv6-86v2-598j
path-to-regexp contains a ReDoS - https://github.com/advisories/GHSA-rhx6-c78j-4q9w
path-to-regexp vulnerable to Regular Expression Denial of Service via multiple route parameters - https://github.com/advisories/GHSA-37ch-88jc-xwx2
fix available via `npm audit fix --force`
Will install express@4.22.3, which is outside the stated dependency range
node_modules/path-to-regexp

qs  <=6.15.3
Severity: high
qs vulnerable to Prototype Pollution - https://github.com/advisories/GHSA-hrpp-h998-j3pp
qs's arrayLimit bypass in comma parsing allows denial of service - https://github.com/advisories/GHSA-w7fw-mjwx-w883
qs's arrayLimit bypass in its bracket notation allows DoS via memory exhaustion - https://github.com/advisories/GHSA-6rw7-vpxm-498p
qs: Denial of Service via Attacker Controlled isBuffer - https://github.com/advisories/GHSA-4mjr-xmp4-gh2g
fix available via `npm audit fix --force`
Will install express@4.22.3, which is outside the stated dependency range
node_modules/qs

send  <0.19.0
send vulnerable to template injection that can lead to XSS - https://github.com/advisories/GHSA-m6fv-jmcg-4jfg
fix available via `npm audit fix --force`
Will install express@4.22.3, which is outside the stated dependency range
node_modules/send
  serve-static  <=1.16.0
  Depends on vulnerable versions of send
  node_modules/serve-static


8 vulnerabilities (3 low, 5 high)

To address issues that do not require attention, run:
  npm audit fix

To address all issues, run:
  npm audit fix --force
código de salida: 1

### 5 · el job del pipeline (npm audit --audit-level=high) sobre las dos versiones
$ npm audit --omit=dev --audit-level=high   # app
código de salida: 1
$ npm audit --omit=dev --audit-level=high   # app-arreglada
found 0 vulnerabilities
código de salida: 0

### 6 · eslint-plugin-security sobre la app arreglada

/demo/app-arreglada/server.js
  31:12  warning  Found readFileSync from package "fs" with non literal argument at index 0  security/detect-non-literal-fs-filename

✖ 1 problem (0 errors, 1 warning)

código de salida: 0
```
