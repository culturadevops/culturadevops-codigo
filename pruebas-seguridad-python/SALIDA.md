# SALIDA — demo del vídeo 802 (seguridad en Python)

Ejecutado 2026-11-05 08:00 en Docker, --rm --cpus 1. Todo ocurre en un mkdtemp del contenedor; el secreto y las tarjetas son FALSOS.

```
$ docker run --rm --cpus 1 -v <esta carpeta>:/demo:ro python:3.13.17-slim sh -c "pip install -q jinja2 werkzeug; cd /tmp && python /demo/demo.py todo"
Jinja2     3.1.6
MarkupSafe 3.0.4
Werkzeug   3.1.9

### 1 · inyección SQL (sqlite3, Python 3.13.17, SQLite 3.46.1)

login usuario='ana' clave='gato123'
  consulta: SELECT nombre FROM usuarios WHERE usuario = 'ana' AND clave = 'gato123'
  A) f-string:   ENTRASTE como Ana
  B) parámetros: ENTRASTE como Ana

login usuario='ana' clave='nolase'
  consulta: SELECT nombre FROM usuarios WHERE usuario = 'ana' AND clave = 'nolase'
  A) f-string:   denegado
  B) parámetros: denegado

login usuario='admin' clave="' OR '1'='1"
  consulta: SELECT nombre FROM usuarios WHERE usuario = 'admin' AND clave = '' OR '1'='1'
  A) f-string:   ENTRASTE como Administración
  B) parámetros: denegado

login usuario="admin' --" clave='cualquiera'
  consulta: SELECT nombre FROM usuarios WHERE usuario = 'admin' --' AND clave = 'cualquiera'
  A) f-string:   ENTRASTE como Administración
  B) parámetros: denegado

buscar 'tecla'
  consulta: SELECT nombre FROM productos WHERE nombre LIKE '%tecla%'
  A) f-string:   [('teclado',)]
  B) parámetros: [('teclado',)]

buscar "x' UNION SELECT numero FROM tarjetas --"
  consulta: SELECT nombre FROM productos WHERE nombre LIKE '%x' UNION SELECT numero FROM tarjetas --%'
  A) f-string:   [('4000-0000-0000-0001 (FALSA)',), ('4000-0000-0000-0002 (FALSA)',)]
  B) parámetros: []

lo que NO se puede parametrizar: un nombre de columna
  ORDER BY ? -> se acepta, pero ordena por un valor fijo, no por la columna
  lista blanca: 'nombre; DROP TABLE productos' in ['id', 'nombre'] -> False

### 2 · XSS con Jinja2 3.1.6
plantilla: <p>{{ comentario }}</p>
dato:      <script>robar(document.cookie)</script>

A) Environment() a secas  autoescape = False
   <p><script>robar(document.cookie)</script></p>

B) Environment(autoescape=True)
   <p>&lt;script&gt;robar(document.cookie)&lt;/script&gt;</p>

C) select_autoescape(['html', 'xml'])
   pagina.html: <p>&lt;script&gt;robar(document.cookie)&lt;/script&gt;</p>
   correo.txt:  <p><script>robar(document.cookie)</script></p>
   from_string: <p>&lt;script&gt;robar(document.cookie)&lt;/script&gt;</p>

D) con autoescape, pero |safe
   <p><script>robar(document.cookie)</script></p>

E) con autoescape, pero Markup(dato del usuario)
   <p><script>robar(document.cookie)</script></p>

F) Markup bien usado: tu HTML fijo + el dato escapado
   <p><b>&lt;script&gt;robar(document.cookie)&lt;/script&gt;</b></p>

G) autoescape no basta en un atributo sin comillas ni en href
   <a href="javascript:robar()">mi web</a>
   <img src=x.png onerror=robar()>

escape() a mano: &lt;script&gt;robar(document.cookie)&lt;/script&gt;

### 3 · path traversal
carpeta temporal: /tmp/demo802-en69c2fr
contenido: publico/leeme.txt  publico/docs/manual.txt  secreto.txt (fuera de publico)

os.path.join('/tmp/demo802-en69c2fr/publico', '/tmp/demo802-en69c2fr/secreto.txt')
  -> '/tmp/demo802-en69c2fr/secreto.txt'
Path('/tmp/demo802-en69c2fr/publico') / '/tmp/demo802-en69c2fr/secreto.txt'
  -> '/tmp/demo802-en69c2fr/secreto.txt'

pide: 'leeme.txt'
  A) os.path.join + open:      lee: hola, soy público   (ruta: /tmp/demo802-en69c2fr/publico/leeme.txt)
  B) resolve + is_relative_to: lee: hola, soy público
  C) werkzeug safe_join:       /tmp/demo802-en69c2fr/publico/leeme.txt

pide: 'docs/manual.txt'
  A) os.path.join + open:      lee: manual en docs   (ruta: /tmp/demo802-en69c2fr/publico/docs/manual.txt)
  B) resolve + is_relative_to: lee: manual en docs
  C) werkzeug safe_join:       /tmp/demo802-en69c2fr/publico/docs/manual.txt

pide: '../secreto.txt'
  A) os.path.join + open:      lee: CLAVE_FALSA_DE_DEMO=1234   (ruta: /tmp/demo802-en69c2fr/publico/../secreto.txt)
  B) resolve + is_relative_to: rechazado: /tmp/demo802-en69c2fr/secreto.txt queda fuera de /tmp/demo802-en69c2fr/publico
  C) werkzeug safe_join:       None

pide: 'docs/../../secreto.txt'
  A) os.path.join + open:      lee: CLAVE_FALSA_DE_DEMO=1234   (ruta: /tmp/demo802-en69c2fr/publico/docs/../../secreto.txt)
  B) resolve + is_relative_to: rechazado: /tmp/demo802-en69c2fr/secreto.txt queda fuera de /tmp/demo802-en69c2fr/publico
  C) werkzeug safe_join:       None

pide: '/tmp/demo802-en69c2fr/secreto.txt'
  A) os.path.join + open:      lee: CLAVE_FALSA_DE_DEMO=1234   (ruta: /tmp/demo802-en69c2fr/secreto.txt)
  B) resolve + is_relative_to: rechazado: /tmp/demo802-en69c2fr/secreto.txt queda fuera de /tmp/demo802-en69c2fr/publico
  C) werkzeug safe_join:       None

pide: 'docs/../leeme.txt'
  A) os.path.join + open:      lee: hola, soy público   (ruta: /tmp/demo802-en69c2fr/publico/docs/../leeme.txt)
  B) resolve + is_relative_to: lee: hola, soy público
  C) werkzeug safe_join:       /tmp/demo802-en69c2fr/publico/leeme.txt

(werkzeug 3.1.9)
```
