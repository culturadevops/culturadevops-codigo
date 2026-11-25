# SALIDA — curso «Python para DevOps desde cero»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-09-22 16:14:33Z`
- Python: `3.11.9`
- sistema: `Windows 10`

## Leccion 01 — El interprete y el entorno

`01_entorno/comprobar_entorno.py` · codigo de salida `0`

```

==============================================================
1.1 · Quien esta ejecutando esto
==============================================================
  version      3.11.9
  ejecutable   C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311\python.exe
  plataforma   win32

==============================================================
1.2 · Estoy dentro de un entorno virtual?
==============================================================
  sys.prefix        C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311
  sys.base_prefix   C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311
  -> en un venv:    False

==============================================================
1.3 · Donde busca Python lo que importas
==============================================================
  sys.path, EN ORDEN. El primero gana:
    0. <repo>\curso-python-devops\01_entorno
    1. C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311\python311.zip
    2. C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311\DLLs
    3. C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311\Lib
    4. C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311
    5. C:\Users\tu-usuario\AppData\Roaming\Python\Python311\site-packages
    ... y 1 mas

==============================================================
1.4 · LA TRAMPA: un fichero tuyo puede tapar la biblioteca estandar
==============================================================
  El directorio actual va el PRIMERO en sys.path.
  Si guardas un fichero llamado json.py y haces `import json`,
  Python importa el TUYO. Y el error que ves no habla de tu fichero:
  habla de que a json le falta una funcion que tu no escribiste.

  Comprobacion rapida de donde sale un modulo:
    json viene de  ->  C:\Users\tu-usuario\AppData\Local\Programs\Python\Python311\Lib\json\__init__.py

==============================================================
1.5 · Variables de entorno: leerlas SIN que reviente
==============================================================
  os.environ.get('PATH') existe: True
  os.environ.get('NO_EXISTE_12345'): None
  con valor por omision: valor-por-defecto

==============================================================
Resumen
==============================================================
  · sys.executable te dice QUE python se esta ejecutando
  · sys.prefix != sys.base_prefix te dice si estas en un venv
  · el directorio actual va primero en sys.path: no llames a tus
    ficheros como modulos de la estandar (json.py, os.py, random.py)
  · os.environ.get() con valor por omision, no os.environ[...]
```

## Leccion 02 — Tipos: mutable contra inmutable

`02_tipos/mutable_vs_inmutable.py` · codigo de salida `0`

```

==============================================================
2.1 · Los tipos que vas a usar de verdad
==============================================================
  42             -> int
  3.5            -> float
  texto          -> str
  True           -> bool
  None           -> NoneType
  [1, 2]         -> list
  (1, 2)         -> tuple
  {'a': 1}       -> dict
  {1, 2}         -> set

==============================================================
2.2 · Inmutable: el numero y la cadena no cambian, se sustituyen
==============================================================
  a = 10; b = a; b += 5   ->   a=10  b=15   (a NO cambio)
  s = 'hola'; t = s; t += ' mundo'  ->  s='hola'  t='hola mundo'

==============================================================
2.3 · Mutable: LA MISMA lista con dos nombres
==============================================================
  lista_a = ['web-01', 'web-02', 'web-03']
  lista_b = ['web-01', 'web-02', 'web-03']
  son el mismo objeto?  id(lista_a)==id(lista_b)  ->  True
  Anadiste a lista_b y aparecio en lista_a. Ese es el fallo.

==============================================================
2.4 · Como se copia de verdad
==============================================================
  original = ['web-01', 'web-02']
  copia    = ['web-01', 'web-02', 'web-03']
  distintos objetos:  True

==============================================================
2.5 · LA TRAMPA DE LA COPIA SUPERFICIAL
==============================================================
  servidores        = [{'nombre': 'web-01', 'puertos': [80, 443]}]
  copia_superficial = [{'nombre': 'web-01', 'puertos': [80, 443]}]
  El diccionario de dentro es EL MISMO. Para copiar en profundidad:
  tras deepcopy y anadir 8080 a la copia:
    servidores = [{'nombre': 'web-01', 'puertos': [80, 443]}]
    honda      = [{'nombre': 'web-01', 'puertos': [80, 443, 8080]}]

==============================================================
2.6 · `is` no es `==`
==============================================================
  x == y  ->  True   (mismo CONTENIDO)
  x is y  ->  False   (mismo OBJETO)
  Usa `is` solo con None, True y False. Para todo lo demas, `==`.

==============================================================
Resumen
==============================================================
  · inmutables: int, float, str, bool, tuple  -> se sustituyen
  · mutables:   list, dict, set               -> se modifican en su sitio
  · asignar NO copia: crea otro nombre para el mismo objeto
  · list() copia un nivel; copy.deepcopy() copia todo
  · `is` compara identidad, `==` compara contenido
```

## Leccion 03 — Cadenas, f-strings y bytes

`03_cadenas/formatear_y_bytes.py` · codigo de salida `0`

```

==============================================================
3.1 · f-strings: lo unico que necesitas para formatear
==============================================================
  api tiene 3 replicas
  cpu al 73.5%            <- porcentaje con 1 decimal
  cpu al 0.735            <- 3 decimales
  |api       |    3|   <- alineado a izquierda y derecha
  1,234,567               <- separador de miles
  'api'                 <- !r pone las comillas (util en logs)

==============================================================
3.2 · La coma del f-string que mas se usa depurando
==============================================================
  puertos=[80, 443]
  replicas * 2 = 6
  Poner = dentro llaves imprime la expresion Y su valor. Oro para depurar.

==============================================================
3.3 · Metodos de cadena que usaras todos los dias
==============================================================
  original      '  ERROR  nginx: connection refused  \n'
  .strip()      'ERROR  nginx: connection refused'
  .lower()      'error  nginx: connection refused'
  .split(':')   ['ERROR  nginx', ' connection refused']
  .startswith   True
  'refused' in  True

==============================================================
3.4 · NO concatenes rutas a mano
==============================================================
  a mano   /etc/nginx/nginx.conf
  pathlib  \etc\nginx\nginx.conf
  y ademas te da las piezas:  .name=nginx.conf  .suffix=.conf
  .parent=\etc\nginx
  En Windows pathlib pone la barra correcta sola. A mano, no.

==============================================================
3.5 · str NO es bytes
==============================================================
  texto  'configuración'   tipo str  longitud 13
  bytes  b'configuraci\xc3\xb3n'   tipo bytes  longitud 14
  La o con tilde ocupa 2 bytes: por eso las longitudes no coinciden.
  de vuelta: 'configuración'

==============================================================
3.6 · LA TRAMPA: decodificar con la codificacion equivocada
==============================================================
  crudo.decode('ascii')  ->  UnicodeDecodeError
    'ascii' codec can't decode byte 0xc3 in position 11: ordinal not in range(128)
  Es el error que ves al leer un log con acentos suponiendo ascii o latin-1.
  Regla: di SIEMPRE encoding='utf-8' al abrir un fichero.

==============================================================
Resumen
==============================================================
  · f-strings para todo; {x=} para depurar
  · pathlib para rutas, nunca concatenar con barras
  · str es texto, bytes es lo que viaja: .encode() y .decode()
  · siempre encoding='utf-8' explicito
```

## Leccion 04 — Colecciones: cual y por que

`04_colecciones/elegir_coleccion.py` · codigo de salida `0`

```

==============================================================
4.1 · Las cuatro, en una linea cada una
==============================================================
  lista  [..]  ordenada, repetible, mutable      -> una secuencia de cosas
  tupla  (..)  ordenada, repetible, INMUTABLE    -> un registro fijo
  dict   {k:v} clave -> valor, mutable           -> un indice
  set    {..}  sin orden, SIN REPETIDOS          -> pertenencia y diferencias

==============================================================
4.2 · Diccionario: leer sin que reviente
==============================================================
  srv['nombre']                  -> web-01
  srv.get('region')              -> None
  srv.get('region', 'us-east-1') -> us-east-1
  srv['region']                  -> KeyError: 'region'
  En un script desatendido, .get() con valor por omision te ahorra la traza.

==============================================================
4.3 · Conjuntos: la herramienta para comparar inventarios
==============================================================
  declarados  ['db-01', 'web-01', 'web-02', 'web-03']
  vivos       ['cache-01', 'db-01', 'web-01', 'web-03']
  declarados - vivos  = ['web-02']   <- deberian estar y NO estan
  vivos - declarados  = ['cache-01']   <- estan y nadie los declaro
  interseccion        = ['db-01', 'web-01', 'web-03']
  Esas dos restas son media herramienta de auditoria, en dos lineas.

==============================================================
4.4 · LA MEDIDA: buscar en una lista contra buscar en un conjunto
==============================================================
  buscando 'host-199999' entre 200,000 elementos (media de muchas repeticiones):
    en una lista           763,715 ns   <- recorre uno a uno
    en un conjunto              27 ns
    en un diccionario           29 ns
    la lista es ~28,426 veces mas lenta que el conjunto
  Con 10 elementos da igual. Con 200.000 es la diferencia entre
  un script de 1 segundo y uno de varios minutos.

==============================================================
4.5 · Comprensiones: filtrar y transformar en una linea
==============================================================
  todos      ['web-01', 'web-02', 'db-01']
  saturados  ['web-01']
  indice     {'web-01': 'activo', 'web-02': 'parado', 'db-01': 'activo'}

==============================================================
4.6 · Tupla: cuando NO quieres que cambie
==============================================================
  punto = ('web-01', 443)
  punto[1] = 80  ->  TypeError: 'tuple' object does not support item assignment
  Y por eso una tupla SI puede ser clave de un diccionario, y una lista no:
  metricas[('web-01','cpu')] = 0.91

==============================================================
Resumen
==============================================================
  · dict cuando busques por clave; set cuando preguntes '¿esta?'
  · buscar en una lista recorre TODO: medido arriba
  · .get(clave, por_omision) en vez de corchetes
  · restar conjuntos es una auditoria en dos lineas
  · tupla para lo que no debe cambiar, y para claves compuestas
```

## Leccion 05 — Flujo y bucles sin romper nada

`05_flujo/recorrer_sin_romper.py` · codigo de salida `0`

```

==============================================================
5.1 · Lo que Python considera falso
==============================================================
  bool(0       ) -> False
  bool(0.0     ) -> False
  bool(''      ) -> False
  bool([]      ) -> False
  bool({}      ) -> False
  bool(set()   ) -> False
  bool(None    ) -> False
  bool(False   ) -> False
  Por eso `if lista:` ya significa 'si la lista NO esta vacia'.
  ⚠ Y por eso `if x:` NO es lo mismo que `if x is not None:` cuando x puede ser 0.

==============================================================
5.2 · LA TRAMPA: borrar mientras recorres
==============================================================
  original  ['web-01','web-02','parado-01','parado-02','db-01']
  resultado ['web-01', 'web-02', 'parado-02', 'db-01']
  Quedo 'parado-02'. Al borrar 'parado-01' todo se corrio una posicion
  y el bucle se salto el siguiente. NO dio error. Solo salio mal.
  la forma correcta (comprension): ['web-01', 'web-02', 'db-01']

==============================================================
5.3 · enumerate y zip: los dos que sustituyen al indice a mano
==============================================================
  1. web-01
  2. web-02
  web-01 -> activo
  web-02 -> parado
  ⚠ zip PARA en la lista mas corta, y no avisa. Si las longitudes
    deben coincidir, usa zip(..., strict=True) (Python 3.10+).
    con strict=True  ->  ValueError: zip() argument 2 is shorter than argument 1

==============================================================
5.4 · for/else: el que casi nadie conoce y aqui viene bien
==============================================================
  'db-02' no esta en la lista   <- el else del for corre si NO hubo break

==============================================================
5.5 · Recorrer un diccionario
==============================================================
  nombre   = web-01
  puerto   = 443
  estado   = activo

==============================================================
Resumen
==============================================================
  · no modifiques una lista mientras la recorres: filtra a una nueva
  · enumerate() para el indice, zip() para ir en paralelo
  · zip se para en la mas corta: strict=True si eso es un fallo
  · for/else corre el else cuando NO hubo break
```

## Leccion 06 — Funciones y el mutable por omision

`06_funciones/argumento_mutable.py` · codigo de salida `0`

```

==============================================================
6.1 · Argumentos: posicionales, con nombre y por omision
==============================================================
  desplegar('api')                          -> api x1 en us-east-1
  desplegar('api', 3)                       -> api x3 en us-east-1
  desplegar('api', region='eu-west-1')      -> api x1 en eu-west-1
  Los que tienen nombre se leen solos dentro de seis meses. Usalos.

==============================================================
6.2 · EL CLASICO: lista como valor por omision
==============================================================
  anadir_mal('web-01')  -> ['web-01']
  anadir_mal('web-02')  -> ['web-01', 'web-02']
  anadir_mal('web-03')  -> ['web-01', 'web-02', 'web-03']
  Esperabas ['web-02'] en la segunda. Salio acumulado.
  La lista por omision se creo UNA vez, al definir la funcion.
  anadir_bien('web-01') -> ['web-01']
  anadir_bien('web-02') -> ['web-02']

==============================================================
6.3 · *args y **kwargs: cuando no sabes cuantos vienen
==============================================================
  [INFO] arranque ok
  [ERROR] fallo al conectar host=db-01 intento=3

==============================================================
6.4 · Devolver varias cosas (es una tupla)
==============================================================
  vivos=2  caidos=1

==============================================================
6.5 · Anotaciones de tipo: documentacion que tu editor lee
==============================================================
  api -> 3
  Python NO las comprueba al ejecutar, pero tu editor y mypy si.
  En un script que va a leer otro, valen su peso en oro.

==============================================================
Resumen
==============================================================
  · valor por omision mutable: usa None y crealo dentro
  · llama con nombre lo que no sea obvio
  · *args y **kwargs para lo variable
  · anota los tipos: es documentacion que no se queda vieja en silencio
```

## Leccion 07 — Ficheros, rutas y codificacion

`07_ficheros/rutas_y_encoding.py` · codigo de salida `0`

```

==============================================================
7.1 · pathlib: rutas que funcionan en los dos sistemas
==============================================================
  ruta      etc\nginx\sitios.conf
  .name     sitios.conf
  .stem     sitios
  .suffix   .conf
  .parent   etc\nginx
  .parts    ('etc', 'nginx', 'sitios.conf')
  La barra correcta la pone pathlib, no tu.

==============================================================
7.2 · Preguntar antes de tocar
==============================================================
  directorio de pruebas: C:\Users\tu-usuario\AppData\Local\Temp\curso_py_bwy8s7i1
  fichero.exists()  antes -> False
  fichero.exists()  ahora -> True
  fichero.stat().st_size  -> 30 bytes

==============================================================
7.3 · Leer: entero, o linea a linea
==============================================================
  read_text() entero (bien para ficheros pequenos):
    web-01 activo
    web-02 parado
  con `with open(...)` linea a linea (bien para un log de 2 GB):
    1: web-01 activo
    2: web-02 parado
  La diferencia importa: read_text() carga TODO en memoria.

==============================================================
7.4 · LA TRAMPA: open() sin encoding
==============================================================
  codificacion por omision de este sistema: cp1252
  escrito en UTF-8: 'configuración añadida'
  leido como latin-1: 'configuraciÃ³n aÃ±adida'   <- NO reventó, pero esta MAL
  leido como ascii:   UnicodeDecodeError
    'ascii' codec can't decode byte 0xc3 in position 11: ordinal not in range(128)
  Regla: encoding='utf-8' SIEMPRE, al leer y al escribir.

==============================================================
7.5 · Recorrer un directorio
==============================================================
  .iterdir()  (solo el primer nivel):
          acentos.txt
          servicios.txt
    [dir] sub
  .rglob('*.conf')  (recursivo, por patron):
    sub\otro.conf

==============================================================
7.6 · Escribir sin dejar el fichero a medias
==============================================================
  se escribe en estado.json.tmp y se renombra a estado.json
  contenido: {"estado": "ok"}
  Si el proceso muere a mitad, el fichero bueno sigue intacto.
  Es lo que hacen por dentro las herramientas serias.

  (limpiado C:\Users\tu-usuario\AppData\Local\Temp\curso_py_bwy8s7i1)

==============================================================
Resumen
==============================================================
  · pathlib para todo: rutas, existencia, tamano, recorrer
  · encoding='utf-8' explicito SIEMPRE
  · read_text() carga entero; `with open()` va linea a linea
  · escribir a .tmp y .replace() es escritura atomica
```

## Leccion 08 — Errores y excepciones

`08_errores/excepciones.py` · codigo de salida `0`

```

==============================================================
8.1 · try / except / else / finally
==============================================================
  dividir(10, 2) -> resultado 5.0
  dividir(10, 0) -> division por cero

==============================================================
8.2 · Captura el tipo que esperas, no todos
==============================================================
  KeyError capturado: falta la clave 'puerto'
  ValueError capturado: invalid literal for int() with base 10: 'no-es-un-numero'
  FileNotFoundError capturado: No such file or directory
  Varios a la vez:  except (KeyError, ValueError) as e:

==============================================================
8.3 · LA TRAMPA: el except pelado
==============================================================
  Esto:
      try:  algo()
      except:  pass

  se traga TAMBIEN:
    · KeyboardInterrupt  -> tu Ctrl+C
    · SystemExit         -> la salida del proceso
    · MemoryError        -> te quedaste sin memoria

  KeyboardInterrupt y SystemExit NO heredan de Exception, precisamente
  para que `except Exception` no los pille:
    issubclass(KeyboardInterrupt, Exception) -> False
    issubclass(ValueError, Exception)        -> True
  Si tienes que capturar amplio, captura `Exception`, nunca pelado.

==============================================================
8.4 · No te comas el error: relanza con contexto
==============================================================
  ErrorDeConfiguracion: /etc/app.conf: el puerto no es un numero
  causa original: ValueError: invalid literal for int() with base 10: 'puerto-mal'
  `raise ... from e` conserva la causa. Sin el `from`, la pierdes.

==============================================================
8.5 · El codigo de salida, que es lo que mira tu tuberia
==============================================================
  sys.exit(0) -> todo bien      (lo que espera CI)
  sys.exit(1) -> algo fallo
  sys.exit(2) -> uso incorrecto (lo que usa argparse)
  Si tu script solo imprime 'ERROR' y sale con 0, CI lo da por bueno.
  (este proceso saldra con 0; ahora mismo sys.argv[0]=excepciones.py)

==============================================================
Resumen
==============================================================
  · captura el tipo concreto; `except Exception` si tienes que ser amplio
  · `except:` pelado se traga el Ctrl+C: es un fallo
  · `raise MiError(...) from e` conserva la causa
  · finally para soltar lo que hayas cogido
  · el codigo de salida es lo que lee CI, no tu mensaje
```

## Leccion 09 — Modulos e imports

`09_modulos/usar_modulo.py` · codigo de salida `0`

```

==============================================================
9.1 · __name__ vale una cosa u otra segun como llegues
==============================================================
  en ESTE fichero, que estoy ejecutando:  __name__ = '__main__'
  en el modulo que acabo de importar:     inventario.__name__ = 'inventario'
  Por eso el bloque `if __name__ == '__main__'` de inventario.py NO se ejecuto
  al importarlo. Si lo corres directo, si.

==============================================================
9.2 · Formas de importar
==============================================================
  import inventario            -> inventario.activos()
  from inventario import activos -> activos()
  import inventario as inv     -> inv.activos()
  ⛔ from inventario import *   -> NO: no sabes que nombres entran

  inventario.VERSION = 1.0
  inventario.activos() = ['web-01', 'db-01']
  inventario.saturados() = ['web-01']

==============================================================
9.3 · De donde salio el modulo
==============================================================
  inventario.__file__ = <repo>\curso-python-devops\09_modulos\inventario.py
  Si un import trae algo que no esperabas, esta linea te lo dice en un segundo.

==============================================================
9.4 · Lo que importa se ejecuta UNA vez
==============================================================
  importado dos veces, es el mismo objeto: True
  Python cachea los modulos en sys.modules:
  'inventario' in sys.modules -> True

==============================================================
9.5 · Un paquete es un directorio con __init__.py
==============================================================
  mi_paquete/
      __init__.py      <- lo que se ejecuta al importar el paquete
      inventario.py
      despliegue.py
  y entonces:  from mi_paquete import inventario

==============================================================
Resumen
==============================================================
  · el codigo suelto de un fichero corre AL IMPORTARLO
  · protegelo con `if __name__ == '__main__':`
  · __file__ te dice de donde salio de verdad un modulo
  · nada de `import *`
```

## Leccion 10 — La biblioteca estandar de DevOps

`10_stdlib/la_caja_de_herramientas.py` · codigo de salida `0`

```

==============================================================
10.1 · subprocess: llamar a un comando y MIRAR el resultado
==============================================================
  returncode  0
  stdout      'hola desde otro proceso'
  stderr      ''
  un comando que falla -> returncode 3
  ⚠ subprocess.run NO lanza excepcion si el comando falla.
    O miras .returncode, o pasas check=True:
    con check=True -> CalledProcessError, returncode 3

==============================================================
10.2 · LA TRAMPA DE SEGURIDAD: shell=True
==============================================================
  Esto, con un nombre que viene de fuera:
      subprocess.run(f'ping {host}', shell=True)
  y host = 'a.com; rm -rf /'  ejecuta LAS DOS cosas.
  La forma segura es pasar una LISTA, sin shell:
      subprocess.run(['ping', host])
  Sin shell no hay interprete que parta por el punto y coma:
  el nombre entero llega como UN argumento, aunque tenga ; o |.

==============================================================
10.3 · json: leer y escribir configuracion
==============================================================
  json.dumps(..., indent=2):
    {
      "servicio": "api",
      "replicas": 3,
      "puertos": [
        80,
        443
      ],
      "activo": true
    }
  json.loads() devuelve un dict: api, 3 replicas
  ⚠ ensure_ascii=False para que los acentos salgan legibles y no como \uXXXX
  json malo -> JSONDecodeError: linea 1, columna 2

==============================================================
10.4 · datetime: siempre con zona horaria
==============================================================
  datetime.now()             2026-09-22 11:14:34.026247   <- 'ingenuo', sin zona
  datetime.now(timezone.utc) 2026-09-22 16:14:34.026247+00:00   <- consciente
  para un log o un nombre de fichero: 2026-09-22T16:14:34Z
  hace una hora: 15:14:34  (restar da un timedelta)
  ⚠ Restar un datetime con zona y otro sin zona lanza TypeError.
    can't subtract offset-naive and offset-aware datetimes

==============================================================
10.5 · logging: en vez de print()
==============================================================
    11:14:34 DEBUG    detalle que solo quieres depurando
    11:14:34 INFO     arranque correcto
    11:14:34 WARNING  el disco va al 85%%
    11:14:34 ERROR    no pude conectar con db-01
  Ventajas sobre print(): nivel, hora, y puedes APAGAR los de abajo
  sin tocar el codigo. Los errores van a stderr si usas basicConfig.

==============================================================
Resumen
==============================================================
  · subprocess.run(LISTA), nunca shell=True con datos de fuera
  · run() no falla solo: mira returncode o pon check=True
  · json.dumps(..., ensure_ascii=False) para acentos legibles
  · datetime SIEMPRE con timezone.utc
  · logging en vez de print: niveles, hora y se puede apagar
```

## Leccion 11 — Clases, lo justo

`11_clases/cuando_una_clase.py` · codigo de salida `0`

```

==============================================================
11.1 · Muchas veces te basta un diccionario
==============================================================
  {'nombre': 'web-01', 'puerto': 443, 'estado': 'activo'}
  Si solo guardas datos y los lees, esto ya esta bien. No hace falta mas.

==============================================================
11.2 · Una clase 'a mano': mucho ruido para guardar tres cosas
==============================================================
  ServidorManual('web-01', 443, 'activo')
  Son nueve lineas para guardar tres campos. Y falta comparar dos.

==============================================================
11.3 · dataclass: lo mismo, sin el ruido
==============================================================
  s1 = Servidor(nombre='web-01', puerto=443, estado='activo', etiquetas=[])
  s3 = Servidor(nombre='db-01', puerto=5432, estado='parado', etiquetas=[])
  s1 == s2  ->  True   <- dataclass te da la comparacion gratis
  s1.url        https://web-01:443     <- @property: se usa sin parentesis
  s3.url        http://db-01:5432
  s3.esta_vivo()  False

==============================================================
11.4 · Por que field(default_factory=list) y no `= []`
==============================================================
  Es el MISMO fallo de la leccion 6: un valor por omision mutable
  se compartiria entre TODAS las instancias.
  s1.etiquetas = ['produccion']
  s2.etiquetas = []   <- vacia, como debe ser
  Con `= []` dataclass directamente se niega a definir la clase.

==============================================================
11.5 · Cuando SI vale la pena una clase
==============================================================
  · cuando los datos y las operaciones sobre ellos van juntos
  · cuando quieres validar al construir (un puerto fuera de rango)
  · cuando vas a tener muchas instancias y quieres comparar u ordenar

  Cuando NO:
  · si es solo un saco de campos que lees una vez -> diccionario
  · si la clase solo tiene metodos y ningun estado -> funciones sueltas

==============================================================
11.6 · Ordenar una lista de objetos
==============================================================
  db-01    http://db-01:5432        vivo=False
  web-01   https://web-01:443       vivo=True
  web-02   http://web-02:80         vivo=True
  vivos: ['web-02', 'web-01']

==============================================================
Resumen
==============================================================
  · @dataclass te da __init__, __repr__ y __eq__ gratis
  · field(default_factory=list) para los mutables
  · @property para lo calculado que se lee como un atributo
  · si no hay comportamiento, un diccionario es mejor que una clase
```

## Leccion 12 — Proyecto: un script para una tuberia

`12_proyecto/revisar_servicios.py` · codigo de salida `1`

```
Revisados 4 servicios (umbral 80%)
  CAIDO      web-02
  SATURADO   web-01  cpu 91%
  SATURADO   cache-01  cpu 88%
WARNING  1 caidos, 2 saturados
```
