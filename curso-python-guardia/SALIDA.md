# SALIDA — curso «Python para la guardia»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-09-22 18:26:13Z`
- Python: `3.11.9`
- sistema: `Windows 10`

## Leccion 01 — Leer sin cargar el log entero

`01_memoria/leer_sin_cargar.py` · codigo de salida `0`

```
== 1.1 · El log de esta noche ==
  app.log   38650 lineas   3.0 MB
  (en produccion son gigas; aqui basta con esto para ver la diferencia)

== 1.2 · LA TRAMPA: read() y readlines() ==
  f.read().splitlines()        3082 errores   pico   9.1 MB   0.02 s
  f.readlines()                3082 errores   pico   5.1 MB   0.02 s
  for linea in f (perezoso)    3082 errores   pico    34 KB   0.01 s
  El resultado es el mismo. La memoria, 274 veces mas.
  Un fichero abierto YA es un iterador de lineas: no hace falta leerlo entero.

== 1.3 · Y encadenar generadores no gasta memoria ==
  errores por servidor: {'web-01': 1005, 'web-02': 1043, 'web-03': 1034}
  pico de memoria: 39 KB para un log de 3.0 MB
  Cada generador pasa UNA linea al siguiente. Nunca hay una lista entera.
```

## Leccion 02 — Partir la linea (y contar lo que se descarta)

`02_parsear/partir_la_linea.py` · codigo de salida `0`

```
== 2.1 · Una linea del log ==
  2026-09-22T02:30:00.000Z INFO    web-03 req-000001 /api/usuarios/{id} 200 170ms

== 2.2 · LA TRAMPA: partir por espacios y coger posiciones ==
  niveles contados: {'INFO': 23392, 'ERROR': 3082, 'WARNING': 266, '(most': 1, '"/srv/app/pool.py",': 1, 'pool': 1}
  Los tres ultimos NO son niveles: son trozos del traceback y de la ruta del
  fichero, contados como si lo fueran.
  lineas sin segundo trozo: 0
  Nadie dijo nada. Los numeros del informe ya estan mal.

== 2.3 · Con una expresion regular con nombres, y CONTANDO lo que no casa ==
  casan: 26740   NO casan: 3
    sin parsear -> Traceback (most recent call last):
    sin parsear ->   File "/srv/app/pool.py", line 88, in obtener
  niveles de verdad: {'INFO': 23392, 'ERROR': 3082, 'WARNING': 266}
  un ejemplo entero: {'hora': '2026-09-22T02:30:00.000Z', 'nivel': 'INFO', 'servidor': 'web-03', 'peticion': 'req-000001', 'ruta': '/api/usuarios/{id}', 'codigo': '200', 'ms': '170'}

== 2.4 · Por que importa contar los descartes ==
  3 de 26743 lineas (0.01%) no encajan.
  Si ese porcentaje sube de golpe, el formato cambio o hay trazas nuevas:
  o sea, es una senal del incidente, no ruido que se tira.
```

## Leccion 03 — Horas, UTC y zonas

`03_tiempo/horas_y_zonas.py` · codigo de salida `0`

```
== 3.1 · La hora del log ==
  2026-09-22T03:12:04.318Z   <- la Z del final: UTC
  strptime sin la Z -> 2026-09-22 03:12:04.318000   tzinfo=None
  Es una fecha INGENUA: no sabe en que zona esta. Y Python la deja pasar.

== 3.2 · LA TRAMPA: comparar una ingenua con una consciente ==
  ingenua < consciente -> TypeError: can't compare offset-naive and offset-aware datetimes
  Este es el error BUENO: se ve. El malo es cuando las dos son ingenuas
  y una estaba en UTC y la otra en tu hora: restas y sale una diferencia falsa.
  con tzinfo=UTC     -> 2026-09-22 03:12:04.318000+00:00
  ahora - incidente  -> 0:07:55.682000

== 3.3 · La guardia la cuentan en hora local ==
  UTC          2026-09-22 03:12:04.318000+00:00
  CDMX         2026-09-21 21:12:04.318000-06:00
  Madrid       2026-09-22 05:12:04.318000+02:00
  'Empezo a las 9 y cuarto de la noche' y '03:12Z' son el MISMO instante.
  Guarda y compara siempre en UTC; traduce solo para escribirlo en el parte.

== 3.4 · LA TRAMPA 2: ordenar fechas como texto ==
  La primera viene de otro servicio, que escribe el mes sin cero delante.
  ordenadas como texto: ['2026-09-22T03:09:00Z', '2026-09-22T03:10:00Z', '2026-9-22T03:08:00Z']
  La mas ANTIGUA queda la ultima: como texto, '2026-9' es mayor que '2026-0'.
  y fromisoformat ni la acepta -> ValueError: Invalid isoformat string: '2026-9-22T03:08:00+00:00'
  strptime si (es mas tolerante) -> ['03:08', '03:09', '03:10']
  ISO-8601 con ceros SI se ordena como texto. Sin ceros, no. Convierte y ordena.

== 3.5 · El cambio de hora: una hora que pasa dos veces ==
  25/10/2026 02:30 en Madrid existe DOS veces:
    la primera  -> 2026-10-25 00:30:00+00:00
    la segunda  -> 2026-10-25 01:30:00+00:00
    diferencia  -> 1:00:00
  Un log en hora local esa madrugada no se puede ordenar. En UTC no pasa:
  UTC no cambia de hora nunca.
  (y la resta entre las dos en local dice 0:00:00)
```

## Leccion 04 — Contar: 3.000 errores que son tres

`04_contar/agrupar_mensajes.py` · codigo de salida `0`

```
== 4.1 · Los errores de la noche ==
  3082 lineas de ERROR de 26739 en total
  una: 0 2367ms error="no se pudo obtener conexion del pool (esperando 5000ms) id=req-016824"

== 4.2 · LA TRAMPA: contar el mensaje tal cual ==
  mensajes DISTINTOS: 3082
       1  web-02 req-016824 /salud 500 2367ms error="no se pudo obtener 
       1  web-02 req-016825 /api/usuarios/{id} 500 2350ms error="no se p
       1  web-02 req-016826 /api/pedidos/{id} 500 2244ms error="no se pu
  Cada mensaje lleva el id de la peticion y los milisegundos dentro,
  asi que casi todos son unicos. El 'top' no dice nada.

== 4.3 · Normalizar y CONTAR PATRONES ==
  patrones distintos: 5
     654  web-<n> <id> /api/usuarios/{id} <n> <n>ms error="no se pudo obtener cone
     617  web-<n> <id> /api/pedidos/{id} <n> <n>ms error="no se pudo obtener conex
     614  web-<n> <id> /api/carrito <n> <n>ms error="no se pudo obtener conexion d
     610  web-<n> <id> /api/pedidos <n> <n>ms error="no se pudo obtener conexion d
     587  web-<n> <id> /salud <n> <n>ms error="no se pudo obtener conexion del poo

== 4.4 · Y ahora cortar por donde duele ==
  por servidor: {'web-01': 1005, 'web-02': 1043, 'web-03': 1034}
  Los tres igual: no es una maquina, es algo compartido (la base de datos).
  por ruta:     {'/api/usuarios/{id}': 654, '/api/pedidos/{id}': 617, '/api/carrito': 614, '/api/pedidos': 610, '/salud': 587}
  por minuto:   {'03:12': 766, '03:13': 779, '03:14': 763, '03:15': 774}
  Cuatro minutos exactos. Eso ya es una ventana para mirar los despliegues.
```

## Leccion 05 — Ventanas: la media de la hora miente

`05_ventanas/la_media_miente.py` · codigo de salida `0`

```
== 5.1 · LA TRAMPA: la media de la hora ==
  3082 errores en 60 minutos -> 51 errores por minuto de media
  Con ese numero en el informe, esto parece ruido de fondo.

== 5.2 · El mismo log, por minuto ==
  03:12   766  ███████████████████████████████
  03:13   779  ███████████████████████████████
  03:14   763  ███████████████████████████████
  03:15   774  ███████████████████████████████
  pico: 03:13 con 779 errores, 15 veces la media
  minutos con algun error: 4 de 60

== 5.3 · Ventana movil: cuando empieza y cuando acaba ==
  primer ERROR: 03:12:00   ultimo: 03:15:59
  duro 3 min 59 s

== 5.4 · Lo que se pone en el parte: el PORCENTAJE, no el numero ==
  minuto antes            0 de  399 peticiones fallan (  0.0%)
  primer minuto malo    767 de 1089 peticiones fallan ( 70.4%)
  minuto de despues       1 de  403 peticiones fallan (  0.2%)
  'Suben los errores' no es un dato. '70% de las peticiones fallan' si.
```

## Leccion 06 — Correlacionar dos logs

`06_correlacionar/dos_fuentes.py` · codigo de salida `0`

```
== 6.1 · La misma peticion, en dos logs ==
  app          2026-09-22T02:30:00.000Z INFO    web-03 req-000001 /api/usuarios/{id} 200 17
  balanceador  2026-09-22T02:30:01.200Z lb-01 "/api/usuarios/{id}" 200 187 id=req-000001 cl
  Otro formato, otro nombre para el id, y los relojes NO estan igual de sincronizados.

== 6.2 · LA TRAMPA: juntarlos por hora ==
  en un segundo cualquiera hay 7.4 peticiones de media
  emparejando por segundo: 26732 parejas, y solo 0 son la peticion buena (0%)
  Ademas los relojes van a 1,2 s de diferencia. Juntar por hora es inventarse parejas.

== 6.3 · Por identificador: un indice y una pasada ==
  indice con 26739 peticiones de app
  unidas: 26739   sin pareja: 0

== 6.4 · Y ahora la pregunta de la guardia ==
  diferencia entre lo que mide el balanceador y lo que mide la app:
    minima 2 ms · maxima 40 ms · media 21.0 ms
  Esa diferencia es el tiempo que la peticion pasa FUERA de tu codigo.
  rutas con 500 vistas desde el balanceador: {'/api/usuarios/{id}': 654, '/api/pedidos/{id}': 617, '/api/carrito': 614}
  Si el balanceador ve 500 y tu app no los tiene, el problema esta antes de tu app.
```

## Leccion 07 — Percentiles

`07_percentiles/la_media_no_sirve.py` · codigo de salida `0`

```
== 7.1 · Las latencias de una hora SIN incidente ==
  19997 peticiones, ninguna de los cuatro minutos malos
  media      182.7 ms
  mediana    154.0 ms
  Con esa media, el panel esta en verde y nadie llama a nadie.

== 7.2 · Los percentiles cuentan otra cosa ==
  p50       154 ms
  p90       244 ms
  p95       255 ms
  p99      1650 ms
  p99.9    2802 ms
  maximo   2986 ms
  El p99 es 9.0 veces la media.

== 7.3 · Cuanta gente es ese 1% ==
  peticiones de mas de 1 s: 297 (1.5%)
  en una hora normal, eso son 297 personas esperando mas de un segundo.
  Y ninguna aparece como error: son 200, con su latencia escondida en la media.

== 7.4 · LA TRAMPA: promediar percentiles ==
  Ahora con la hora ENTERA, incidente incluido, que es lo que ve tu panel.
  p95 de cada minuto, y luego su media: 509 ms
  p95 de verdad, sobre las 26739 peticiones: 3172 ms
  Un percentil no se puede promediar: hay que recalcularlo sobre los datos.
  Por eso los paneles que guardan 'el p95 por minuto' mienten al juntar la hora.

== 7.5 · quantiles de la biblioteca estandar ==
  statistics.quantiles(lat, n=100)[94] -> 255 ms  (p95)
  statistics.quantiles(lat, n=100)[98] -> 1643 ms  (p99)
  Interpola entre dos valores, asi que puede no coincidir con el dato exacto.
```

## Leccion 08 — Logs en JSON rotos

`08_json/logs_json.py` · codigo de salida `0`

```
== 8.1 · El fichero de esta noche (JSON por linea) ==
  1: {"ts": "2026-09-22T03:11:58Z", "nivel": "INFO", "ruta": "/api/pedidos"
  2: {"ts": "2026-09-22T03:12:01Z", "nivel": "ERROR", "ruta": "/api/pedidos
  3: {"ts": "2026-09-22T03:12:01Z", "nivel": "ERROR", "ru
  4: Traceback (most recent call last):
  5: {"ts": "2026-09-22T03:12:02Z", "nivel": "INFO", "ruta": "/salud", "cod

== 8.2 · LA TRAMPA: json.loads sin red ==
  JSONDecodeError en la linea 3: Unterminated string starting at
  Tres de la manana, el script se muere, y no sabes si iba por el principio
  o por el final del fichero.

== 8.3 · LA TRAMPA 2: el except que se lo traga todo ==
  lineas leidas: 3 de 5. Y el script no dijo NADA.
  Callar los errores es peor que reventar: el informe sale con menos datos
  y con la misma cara de seguridad.

== 8.4 · Bien: se salta, se CUENTA y se guarda una muestra ==
  filas buenas: 3   rotas: 2
    linea 3: Unterminated string starting at  ->  {"ts": "2026-09-22T03:12:01Z", "nivel": 
    linea 4: Expecting value  ->  Traceback (most recent call last):
  40% del fichero no se pudo leer. Eso va en el informe.

== 8.5 · Y la clave que a veces no esta ==
  filas sin 'ms': 1
  sumar f['ms'] -> KeyError: 'ms'
  con .get('ms', 0): 3299 ms ... repartido entre 3 filas
  pero la media de verdad es sobre las 2 que SI la tienen: 1650 ms
  Poner 0 donde no hay dato no es un arreglo: es inventarse una medicion.
  niveles: {'INFO': 2, 'ERROR': 1}
```

## Leccion 09 — Rotados y comprimidos

`09_rotados/ficheros_rotados.py` · codigo de salida `0`

```
== 9.1 · Lo que hay en la carpeta ==
  app.log           1934.9 KB
  app.log.1          294.1 KB
  app.log.10.gz       37.5 KB
  app.log.11.gz       37.6 KB
  app.log.2.gz        37.4 KB
  app.log.3.gz        37.5 KB

== 9.2 · LA TRAMPA: ordenar por nombre ==
  sorted():  ['app.log', 'app.log.1', 'app.log.10.gz', 'app.log.11.gz', 'app.log.2.gz', 'app.log.3.gz']
  app.log.10 queda ANTES de app.log.2: es orden de texto, no de numero.
  Y app.log, el actual, queda el primero cuando es el ULTIMO en el tiempo.
  del mas viejo al mas nuevo: ['app.log.11.gz', 'app.log.10.gz', 'app.log.3.gz', 'app.log.2.gz', 'app.log.1', 'app.log']

== 9.3 · Abrir .gz sin descomprimir a disco ==
  app.log.11.gz      4000 lineas
  app.log.10.gz      3984 lineas
  app.log.3.gz       3986 lineas
  app.log.2.gz       3978 lineas
  app.log.1          3978 lineas
  app.log           22802 lineas
  total: 42728 lineas de 6 ficheros, sin descomprimir nada a disco

== 9.4 · Una sola secuencia de lineas ==
  primera linea leida: 2026-09-22T02:30:00.000Z  (del fichero mas viejo)
  errores en TODA la rotacion: 3210
  Un generador que encadena ficheros: el resto del analisis no se entera
  de si venian comprimidos, rotados o de un solo fichero.

== 9.5 · El detalle que muerde: el comprimido no se puede recorrer al reves ==
  app.log.2.gz: 37.4 KB comprimido
  descomprimido son 290.2 KB: 7.8 veces mas
  Para ver el final de un .gz hay que descomprimirlo entero. No hay atajo.
```

## Leccion 10 — Solo el final de un log enorme

`10_final/solo_el_final.py` · codigo de salida `0`

```
== 10.1 · El log de la semana ==
  app.log   17.8 MB
  (en la maquina de verdad seran gigas; la idea es la misma)

== 10.2 · Tres formas de ver las ultimas 20 lineas ==
  read().splitlines()[-20:]       38.8 ms   20 lineas
  deque(f, maxlen=20)             18.6 ms   20 lineas
  seek desde el final              0.2 ms   20 lineas
  Las tres dan lo mismo. Las dos primeras LEEN LOS 17.8 MB para eso.
  El seek lee 64 KB. Y la diferencia crece con el tamano del fichero.

== 10.3 · La ultima linea, que es lo que miras primero ==
  2026-09-22T12:29:59.950Z INFO    web-02 req-242554 /salud 200 238ms

== 10.4 · Lo mismo para 'que paso entre las 03:10 y las 03:20' ==
  7133 lineas en la ventana, en 3 ms
  El break es el truco: en un log ordenado, pasada la ventana no hay nada mas.
  Sin el break, esto recorre el fichero entero para nada.
```

## Leccion 11 — Muestreo: no te mientas

`11_muestreo/no_te_mientas.py` · codigo de salida `0`

```
== 11.1 · La trampa de las primeras mil ==
  head -1000                   1000 lineas     0.0% errores   latencia media    167 ms
  el fichero entero           26739 lineas    11.5% errores   latencia media    541 ms
  El incidente esta en el minuto 42 de la hora. En las primeras mil lineas
  no ha pasado nada todavia: 'esto esta tranquilo' y a dormir.

== 11.2 · Y la de las ultimas mil ==
  tail -1000                   1000 lineas     0.0% errores   latencia media    175 ms
  Tampoco: el incidente ya paso. Las dos muestras dicen que todo va bien.

== 11.3 · Una muestra de verdad: repartida ==
  1 de cada 2                 13370 lineas    11.5% errores   latencia media    541 ms
  1 de cada 10                 2674 lineas    11.6% errores   latencia media    550 ms
  1 de cada 50                  535 lineas    12.3% errores   latencia media    571 ms
  Repartida por todo el fichero, hasta 1 de cada 50 acierta el porcentaje.
  La muestra vale si es del TODO. Un trozo contiguo no es una muestra:
  es una ventana de tiempo, y en un incidente eso lo cambia todo.

== 11.4 · Lo que casi siempre es mejor: contar entero ==
  contar los 3082 errores del fichero entero: 3 ms
  para 2.2 MB. A las tres de la manana,
  el tiempo no lo gasta la maquina: lo gastas tu decidiendo si fiarte.
```

## Leccion 12 — Proyecto: triaje.py

`12_proyecto/escenario.py` · codigo de salida `0`

```
== los ficheros ==
  app.log          2.2 MB
  app.log.1        0.6 MB
  app.log.2.gz     0.1 MB

== 1 · La hora entera, que es lo primero que haces ==
  $ python triaje.py app.log
  == triaje de 1 fichero(s) [inicio -> fin] ==
    lineas leidas   26740  (descartadas 1: Traceback (most recent call last):)
    peticiones      26739
    errores         3082  (11.53%)
    latencia        p50 176 ms · p95 3172 ms · p99 3988 ms
    ventana mala    03:12 -> 03:15 (peor: 03:13 con 779)
    por servidor    {'web-02': 1043, 'web-03': 1034, 'web-01': 1005}
    rutas           {'/api/usuarios/{id}': 654, '/api/pedidos/{id}': 617, '/api/carrito': 614}
    patrones de error mas repetidos:
       3082  error="no se pudo obtener conexion del pool (esperando <n>ms) id
    -> codigo de salida 1
  [0.1 s · codigo 1]

== 2 · Solo la ventana del aviso ==
  $ python triaje.py app.log --desde 03:10 --hasta 03:20
  == triaje de 1 fichero(s) [03:10 -> 03:20] ==
    lineas leidas   26740  (descartadas 1: Traceback (most recent call last):)
    peticiones      7133
    errores         3082  (43.21%)
    latencia        p50 1078 ms · p95 3926 ms · p99 4146 ms
    ventana mala    03:12 -> 03:15 (peor: 03:13 con 779)
    por servidor    {'web-02': 1043, 'web-03': 1034, 'web-01': 1005}
    rutas           {'/api/usuarios/{id}': 654, '/api/pedidos/{id}': 617, '/api/carrito': 614}
    patrones de error mas repetidos:
       3082  error="no se pudo obtener conexion del pool (esperando <n>ms) id
    -> codigo de salida 1
  [0.1 s · codigo 1]

== 3 · Un rato tranquilo: asi se ve cuando NO pasa nada ==
  $ python triaje.py app.log --desde 02:40 --hasta 02:50
  == triaje de 1 fichero(s) [02:40 -> 02:50] ==
    lineas leidas   26740  (descartadas 1: Traceback (most recent call last):)
    peticiones      4395
    errores         0  (0.0%)
    latencia        p50 153 ms · p95 256 ms · p99 1769 ms
    sin minutos por encima del umbral
    -> codigo de salida 0
  [0.1 s · codigo 0]

== 4 · Todos los ficheros, incluido el .gz ==
  $ python triaje.py app.log*
  == triaje de 3 fichero(s) [inicio -> fin] ==
    lineas leidas   42787  (descartadas 1: Traceback (most recent call last):)
    peticiones      42786
    errores         3082  (7.2%)
    latencia        p50 167 ms · p95 2625 ms · p99 3878 ms
    ventana mala    03:12 -> 03:15 (peor: 03:13 con 779)
    por servidor    {'web-02': 1043, 'web-03': 1034, 'web-01': 1005}
    rutas           {'/api/usuarios/{id}': 654, '/api/pedidos/{id}': 617, '/api/carrito': 614}
    patrones de error mas repetidos:
       3082  error="no se pudo obtener conexion del pool (esperando <n>ms) id
    -> codigo de salida 1
  [0.1 s · codigo 1]

== 5 · Para pegarlo en el ticket ==
  $ python triaje.py app.log --desde 03:12 --hasta 03:15 --json
  {
    "lineas": 26740,
    "descartadas": 1,
    "peticiones": 4331,
    "errores": 3082,
    "porcentaje_error": 71.16,
    "p50_ms": 2518,
    "p95_ms": 4036,
    "p99_ms": 4171,
    "peor_minuto": "03:13",
    "errores_en_ese_minuto": 779,
    "ventana": [
      "03:12",
      "03:15"
    ],
    "patrones": [
      [
        "error=\"no se pudo obtener conexion del pool (esperando <n>ms) id=<id>\"",
        3082
      ]
    ],
    "servidores": {
      "web-02": 1043,
      "web-03": 1034,
      "web-01": 1005
    },
    "rutas": {
      "/api/usuarios/{id}": 654,
      "/api/pedidos/{id}": 617,
      "/api/carrito": 614
    }
  }
  [0.1 s · codigo 1]
```
