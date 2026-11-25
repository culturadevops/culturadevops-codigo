$ python --version
Python 3.11.9
$ grep -n "f\"SELECT" login.py
16:    q = f"SELECT nombre FROM usuarios WHERE nombre = '{nombre}' AND clave = '{clave}'"

$ python login.py ana malaclave
acceso denegado
$ python login.py "ana' --" cualquiera
ENTRÓ como ana

$ bandit -q login.py
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
Severity: Low   Confidence: High
Location: .\login.py:2:0
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
Severity: Medium   Confidence: Low
Location: .\login.py:16:8
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
Severity: High   Confidence: High
Location: .\login.py:21:4
$ grep -n CLAVE_ADMIN login.py   # la contraseña escrita en el código: bandit no la marcó
5:CLAVE_ADMIN = "SuperSecreta2026"
$ # la misma línea, con la variable en inglés
$ bandit -q login_en.py | grep B105
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'SuperSecreta2026'

$ # arreglo: consulta con parámetros (?), clave en variable de entorno, subprocess sin shell
$ python login.py "ana' --" cualquiera
acceso denegado
$ python login.py ana x9!kL2
ENTRÓ como ana
$ bandit -q login.py
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
Severity: Low   Confidence: High
>> Issue: [B607:start_process_with_partial_path] Starting a process with a partial executable path
Severity: Low   Confidence: High
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
Severity: Low   Confidence: High
(código de salida de bandit: 0 con -lll, solo severidad alta)

$ # ¿existen en PyPI? dos reales y dos nombres inventados, del tipo que alucina un modelo
requests: existe
flask-login: existe
flask-secure-login-helper: NO EXISTE (HTTP 404)
sqlite3-safe-query: NO EXISTE (HTTP 404)
$ bandit --version
bandit 1.8.6
