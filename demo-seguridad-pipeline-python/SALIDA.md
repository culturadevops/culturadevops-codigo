# Salida real — seguridad en el pipeline para Python

Ejecutado el 2026-10-23T17:53Z en python:3.13-slim.

```
### versiones
bandit 1.9.4
pip-audit 2.10.1
1.182.1

### 1 · bandit sobre la app vulnerable (todas las severidades)
$ bandit -r app/
Test results:
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: app/app.py:5:0
4	import sqlite3
5	import subprocess
6	

--------------------------------------------------
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'admin123'
   Severity: Low   Confidence: Medium
   CWE: CWE-259 (https://cwe.mitre.org/data/definitions/259.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b105_hardcoded_password_string.html
   Location: app/app.py:15:11
14	STRIPE_API_KEY = "CLAVE_STRIPE_FALSA_DE_EJEMPLO"
15	password = "admin123"
16	

--------------------------------------------------
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Medium
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
   Location: app/app.py:23:26
22	    # Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
23	    filas = con.execute(f"SELECT id, nombre, precio FROM productos WHERE nombre = '{nombre}'").fetchall()
24	    return {"productos": filas}

--------------------------------------------------
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
   Severity: High   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b602_subprocess_popen_with_shell_equals_true.html
   Location: app/app.py:31:13
30	    # Fallo 2: inyección de comandos (shell=True con texto del usuario)
31	    salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
32	    return salida

--------------------------------------------------
>> Issue: [B506:yaml_load] Use of unsafe yaml load. Allows instantiation of arbitrary objects. Consider yaml.safe_load().
   Severity: Medium   Confidence: High
   CWE: CWE-20 (https://cwe.mitre.org/data/definitions/20.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b506_yaml_load.html
   Location: app/app.py:46:12
45	    # Extra: yaml.load sin Loader seguro
46	    datos = yaml.load(request.data, Loader=yaml.Loader)
47	    return {"ok": bool(datos)}

--------------------------------------------------

Code scanned:

### 2 · pip-audit sobre requirements.txt
$ pip-audit -r app/requirements.txt
Found 41 known vulnerabilities in 5 packages
Name     Version ID              Fix Versions
-------- ------- --------------- -------------
flask    3.1.2   PYSEC-2026-2151 3.1.3
flask    3.1.2   PYSEC-2026-2151 3.1.3
pyyaml   5.3.1   PYSEC-2021-142  5.4
pyyaml   5.3.1   PYSEC-2021-142  5.4
requests 2.19.1  PYSEC-2018-28   2.20.0
requests 2.19.1  PYSEC-2018-28   2.20.0
requests 2.19.1  PYSEC-2023-74   2.31.0
requests 2.19.1  PYSEC-2023-74   2.31.0
requests 2.19.1  PYSEC-2026-1873 2.32.0
requests 2.19.1  PYSEC-2026-1872 2.32.4
requests 2.19.1  PYSEC-2026-2275 2.33.0
requests 2.19.1  PYSEC-2026-1873 2.32.0
requests 2.19.1  PYSEC-2026-1872 2.32.4
requests 2.19.1  PYSEC-2026-2275 2.33.0
idna     2.7     PYSEC-2024-60   3.7
idna     2.7     PYSEC-2024-60   3.7
idna     2.7     PYSEC-2026-215  3.15
idna     2.7     PYSEC-2026-215  3.15
urllib3  1.23    PYSEC-2019-133  1.24.2
urllib3  1.23    PYSEC-2019-132  1.24.3
urllib3  1.23    PYSEC-2020-148  1.25.9
urllib3  1.23    PYSEC-2019-133  1.24.2
urllib3  1.23    PYSEC-2020-148  1.25.9
urllib3  1.23    PYSEC-2019-132  1.24.3
urllib3  1.23    PYSEC-2026-1995 1.26.19,2.2.2
urllib3  1.23    PYSEC-2023-192  1.26.17,2.0.6
urllib3  1.23    PYSEC-2023-192  1.26.17,2.0.6
urllib3  1.23    PYSEC-2023-207  1.24.2
urllib3  1.23    PYSEC-2023-212  1.26.18,2.0.7
urllib3  1.23    PYSEC-2023-207  1.24.2
urllib3  1.23    PYSEC-2023-212  1.26.18,2.0.7
urllib3  1.23    PYSEC-2026-1999 2.5.0
urllib3  1.23    PYSEC-2026-1994 2.6.0
urllib3  1.23    PYSEC-2026-1996 2.6.3
urllib3  1.23    PYSEC-2026-141  2.7.0
urllib3  1.23    PYSEC-2026-141  2.7.0
urllib3  1.23    PYSEC-2026-1999 2.5.0
urllib3  1.23    PYSEC-2026-1995 1.26.19,2.2.2
urllib3  1.23    PYSEC-2026-1994 2.6.0
urllib3  1.23    PYSEC-2026-1996 2.6.3
urllib3  1.23    PYSEC-2026-4177 2.8.0

### 3 · semgrep con las reglas de Python y Flask
$ semgrep --config p/python --config p/flask app/
                   
                   
┌─────────────────┐
│ 7 Code Findings │
└─────────────────┘
              
    app/app.py
    ❯❱ python.django.security.injection.sql.sql-injection-using-db-cursor-execute.sql-injection-db-cursor-execute
          ❰❰ Blocking ❱❱
          User-controlled data from a request is passed to 'execute()'. This could lead to a SQL injection and
          therefore protected information could be leaked. Instead, use django's QuerySets, which are built   
          with query parameterization and therefore not vulnerable to sql injection. For example, you could   
          use `Entry.objects.filter(date=2006)`.                                                              
          Details: https://sg.run/qx7y                                                                        
                                                                                                              
           20┆ nombre = request.args.get("nombre", "")
           21┆ con = sqlite3.connect(DB)
           22┆ # Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
           23┆ filas = con.execute(f"SELECT id, nombre, precio FROM productos WHERE nombre =
               '{nombre}'").fetchall()                                                      
   
   ❯❯❱ python.flask.security.injection.tainted-sql-string.tainted-sql-string
          ❰❰ Blocking ❱❱
          Detected user input used to manually construct a SQL string. This is usually bad practice because 
          manual construction could accidentally result in a SQL injection. An attacker could use a SQL     
          injection to steal or modify contents of the database. Instead, use a parameterized query which is
          available by default in most database engines. Alternatively, consider using an object-relational 
          mapper (ORM) such as SQLAlchemy which will protect your queries.                                  
          Details: https://sg.run/JxZj                                                                      
                                                                                                            
           23┆ filas = con.execute(f"SELECT id, nombre, precio FROM productos WHERE nombre =
               '{nombre}'").fetchall()                                                      
   
   ❯❯❱ python.flask.security.injection.subprocess-injection.subprocess-injection
          ❰❰ Blocking ❱❱
          Detected user input entering a `subprocess` call unsafely. This could result in a command injection 
          vulnerability. An attacker could use this vulnerability to execute arbitrary commands on the host,  
          which allows them to download malware, scan sensitive data, or run any command they wish on the     
          server. Do not let users choose the command to run. In general, prefer to use Python API versions of
          system commands. If you must use subprocess, use a dictionary to allowlist a set of commands.       
          Details: https://sg.run/5gW3                                                                        
                                                                                                              
           31┆ salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
   
   ❯❯❱ python.lang.security.dangerous-subprocess-use.dangerous-subprocess-use
          ❰❰ Blocking ❱❱
          Detected subprocess function 'check_output' with user controlled data. A malicious actor could
          leverage this to perform command injection. You may consider using 'shlex.escape()'.          
          Details: https://sg.run/NWxp                                                                  
                                                                                                        
           31┆ salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
   
   ❯❯❱ python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
          ❰❰ Blocking ❱❱
          Found 'subprocess' function 'check_output' with 'shell=True'. This is dangerous because this call 
          will spawn the command using a shell process. Doing so propagates current shell settings and      
          variables, which makes it much easier for a malicious actor to execute commands. Use 'shell=False'
          instead.                                                                                          
          Details: https://sg.run/J92w                                                                      
                                                                                                            
           ▶▶┆ Autofix ▶ False
           31┆ salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
   
   ❯❯❱ python.flask.security.injection.path-traversal-open.path-traversal-open
          ❰❰ Blocking ❱❱
          Found request data in a call to 'open'. Ensure the request data is validated or sanitized, otherwise
          it could result in path traversal attacks.                                                          
          Details: https://sg.run/PJRW                                                                        
                                                                                                              
           39┆ with open(os.path.join(FACTURAS, archivo)) as f:
   
   ❯❯❱ python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load
          ❰❰ Blocking ❱❱
          Detected a possible YAML deserialization vulnerability. `yaml.unsafe_load`, `yaml.Loader`,          
          `yaml.CLoader`, and `yaml.UnsafeLoader` are all known to be unsafe methods of deserializing YAML. An
          attacker with control over the YAML input could create special YAML input that allows the attacker  
          to run arbitrary Python code. This would allow the attacker to steal files, download and install    
          malware, or otherwise take over the machine. Use `yaml.safe_load` or `yaml.SafeLoader` instead.     
          Details: https://sg.run/we9Y                                                                        
                                                                                                              
           ▶▶┆ Autofix ▶ yaml.load(request.data, Loader=yaml.Loader)
           46┆ datos = yaml.load(request.data, Loader=yaml.Loader)


### 3b · semgrep con las reglas de secretos (la clave de Stripe)
$ semgrep --config p/secrets app/
                  
                  
┌────────────────┐
│ 1 Code Finding │
└────────────────┘
              
    app/app.py
   ❯❯❱ generic.secrets.security.detected-stripe-api-key.detected-stripe-api-key
          ❰❰ Blocking ❱❱
          Stripe API Key detected     
          Details: https://sg.run/dKd5
                                      
           14┆ STRIPE_API_KEY = "CLAVE_STRIPE_FALSA_DE_EJEMPLO"


### 3c · bandit SOLO con severidad alta (-lll): ¿cuántos de los 4 fallos ve?
$ bandit -r app/ -lll
test_id,issue_severity,issue_cwe,issue_text
B602,HIGH,https://cwe.mitre.org/data/definitions/78.html,"subprocess call with shell=True identified

### 4 · el job del pipeline sobre la app vulnerable
$ ./ci-seguridad.sh app
== bandit (código, umbral -ll)
Run started:2026-10-23 17:53:40.254166+00:00

Test results:
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Medium
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
   Location: ./app.py:23:26
22	    # Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
23	    filas = con.execute(f"SELECT id, nombre, precio FROM productos WHERE nombre = '{nombre}'").fetchall()
24	    return {"productos": filas}

--------------------------------------------------
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
   Severity: High   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b602_subprocess_popen_with_shell_equals_true.html
   Location: ./app.py:31:13
30	    # Fallo 2: inyección de comandos (shell=True con texto del usuario)
31	    salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
32	    return salida

--------------------------------------------------
>> Issue: [B506:yaml_load] Use of unsafe yaml load. Allows instantiation of arbitrary objects. Consider yaml.safe_load().
   Severity: Medium   Confidence: High
   CWE: CWE-20 (https://cwe.mitre.org/data/definitions/20.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b506_yaml_load.html
   Location: ./app.py:46:12
45	    # Extra: yaml.load sin Loader seguro
46	    datos = yaml.load(request.data, Loader=yaml.Loader)
47	    return {"ok": bool(datos)}

--------------------------------------------------

Code scanned:
	Total lines of code: 32
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 2
		Medium: 2
		High: 1
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 2
		High: 3
Files skipped (0):
== semgrep (reglas de Python, Flask y secretos)
semgrep: hay hallazgos
== pip-audit (dependencias de requirements.txt)
urllib3  1.23    PYSEC-2026-1995 1.26.19,2.2.2
urllib3  1.23    PYSEC-2026-1994 2.6.0
urllib3  1.23    PYSEC-2026-1996 2.6.3
urllib3  1.23    PYSEC-2026-4177 2.8.0
PIPELINE: FALLA (hay hallazgos de seguridad)
código de salida: 1

### 5 · el mismo job sobre la app arreglada
$ ./ci-seguridad.sh app-arreglada
== bandit (código, umbral -ll)
== semgrep (reglas de Python, Flask y secretos)
== pip-audit (dependencias de requirements.txt)
No known vulnerabilities found
PIPELINE: PASA
código de salida: 0

### 6 · semgrep sobre la app arreglada
código de salida: 0

### 7 · un nosec con texto detrás de los códigos
import subprocess
subprocess.check_output(["ping", "-c", "1", "127.0.0.1"])  # nosec B603 B607 -- argumentos fijos, IP validada
$ bandit /tmp/nosec.py
[manager]	WARNING	Test in comment: argumentos is not a test name or id, ignoring
[manager]	WARNING	Test in comment: fijos is not a test name or id, ignoring
[manager]	WARNING	Test in comment: IP is not a test name or id, ignoring
[manager]	WARNING	Test in comment: validada is not a test name or id, ignoring
```
