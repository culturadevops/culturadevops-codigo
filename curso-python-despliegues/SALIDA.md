# SALIDA — curso «Python para automatizar despliegues»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-09-22 17:00:29Z`
- Python: `3.11.9`
- sistema: `Windows 10`

## Leccion 01 — subprocess: el comando fallo y seguiste

`01_subprocess/ejecutar_comandos.py` · codigo de salida `0`

```
== 1.1 · LA TRAMPA: run() sin check=True no se queja ==
compilando...
  codigo de salida del comando: 3
  y el script sigue: 'desplegado con exito'   <- mentira

== 1.2 · check=True: si falla, se para ==
  CalledProcessError: codigo 3. No se despliega.

== 1.3 · LA TRAMPA: shell=True con un dato que viene de fuera ==
  rama = 'main & echo INYECTADO'
  shell=True  -> desplegando main
  shell=True  -> INYECTADO
  lista       -> argumentos: ['main & echo INYECTADO']
  Con lista no hay shell: el dato llega entero, como UN argumento.

== 1.4 · Un comando colgado cuelga tu despliegue: timeout ==
  TimeoutExpired a los 1.0 s (sin timeout: 30 s, o nunca)

== 1.5 · El motivo del fallo esta en stderr ==
  stdout: 'paso 1 ok'
  stderr: 'error: disco lleno'
  Si solo guardas stdout, en el log queda 'paso 1 ok' y el porque se pierde.
```

## Leccion 02 — Dry-run: un simulacro que simule

`02_dry_run/simulacro.py` · codigo de salida `0`

```
== 2.1 · LA TRAMPA: el dry-run dice que todo bien ==
  [dry-run] copiaria app.txt a releases/v2
  dry-run OK. Vamos de verdad:
  FileNotFoundError: biuld\app.txt
  El simulacro no paso por la linea con la errata. No simulo nada.
  Y encima dejo esto a medias: releases/ = ['v2'], vacia: True

== 2.2 · El plan se calcula igual con y sin dry-run ==
  plan invalido: no existe biuld\app.txt
  Ahora la errata sale en el SIMULACRO, que es donde tiene que salir.

== 2.3 · Con la ruta buena: simulacro y luego de verdad ==
  plan invalido: releases/v2 ya existe
  El plan tambien caza la basura del intento fallido. La quito y repito:
  [dry-run] crear releases/v2
  [dry-run] copiar build\app.txt -> releases/v2
  [hecho]   crear releases/v2
  [hecho]   copiar build\app.txt -> releases/v2
  releases/: ['v2']
```

## Leccion 03 — Idempotencia: se va a ejecutar dos veces

`03_idempotencia/dos_veces.py` · codigo de salida `0`

```
== 3.1 · LA TRAMPA: anadir una linea ==
  tras 2 ejecuciones, 'cache=on' aparece 2 veces:
    puerto=8080
    cache=on
    cache=on

== 3.2 · Idempotente: 'que quede asi', no 'haz esto' ==
  ejecucion 1: cambiado
  ejecucion 2: sin cambios
  ejecucion 3: sin cambios
  'cache=on' aparece 1 vez
  y si piden cache=off: cambiado -> ['puerto=8080', 'cache=off']
  Decir 'cambiado / sin cambios' es lo que hace Ansible. Y es lo que te deja
  saber si el segundo despliegue toco algo.

== 3.3 · La otra cara: crear lo que ya existe ==
  mkdir() la segunda vez -> FileExistsError: el reintento revienta
  mkdir(exist_ok=True) la segunda vez -> nada. Idempotente.
```

## Leccion 04 — Escritura atomica

`04_atomico/escribir_sin_romper.py` · codigo de salida `0`

```
== 4.1 · LA TRAMPA: escribir encima ==
  el proceso murio a mitad de escribir
  config.json ahora: '{"version": "v2", "replicas": 5'
  la app al arrancar: JSONDecodeError: Expecting ',' delimiter
  Ya no tienes ni la version vieja ni la nueva.

== 4.2 · Atomico: temporal al lado y os.replace ==
  el proceso murio a mitad de escribir... el TEMPORAL
  config.json sigue: {'version': 'v1', 'replicas': 3, 'puerto': 8080}
  sin corte:         {'version': 'v2', 'replicas': 5, 'puerto': 8080, 'cache': True}
  .tmp que quedan: []
  (el del corte lo piso la escritura buena; si nadie vuelve a escribir,
   queda ahi: limpialo al arrancar)
  os.replace es atomico dentro del MISMO sistema de archivos.
  Por eso el temporal va al lado, no en /tmp.
```

## Leccion 05 — Reintentos: cuales, cuantos y cuanto esperar

`05_reintentos/reintentar_bien.py` · codigo de salida `0`

```
== 5.1 · Un servicio que falla dos veces y luego contesta ==
    intento 1: ConnectionError -> espero 32 ms
    intento 2: ConnectionError -> espero 30 ms
  -> imagen app:v2 descargada

== 5.2 · LA TRAMPA: reintentarlo TODO ==
    intento 1: ValueError -> espero 100 ms
    intento 2: ValueError -> espero 200 ms
    intento 3: ValueError -> espero 400 ms
    intento 4: ValueError -> espero 800 ms
  ValueError tras 5 intentos y 1.5 s: replicas='cinco' no es un numero
  Un error de config no se arregla esperando. Solo se retrasa el aviso.
  solo transitorios: ValueError al primer intento (0 ms)

== 5.3 · LA TRAMPA: reintentar algo que NO es idempotente ==
    intento 1: TimeoutError -> espero 0 ms
  sin clave:        releases = ['v2', 'v2']
    intento 1: TimeoutError -> espero 0 ms
  con clave de idempotencia: releases = ['v2']
  Un timeout NO significa que no se hizo. Significa que no sabes.

== 5.4 · Por que el azar (jitter): 5 clientes caen a la vez ==
  sin jitter: el 3er reintento de cada cliente llega en ms [700, 700, 700, 700, 700]
  con jitter: el 3er reintento de cada cliente llega en ms [281, 212, 273, 411, 435]
  Sin azar, todos vuelven al mismo milisegundo y lo vuelven a tumbar.
```

## Leccion 06 — Timeouts: por defecto, para siempre

`06_timeouts/sin_limite.py` · codigo de salida `0`

```
== 6.1 · El valor por defecto ==
  socket.getdefaulttimeout() -> None   <- sin limite

== 6.2 · LA TRAMPA: urlopen sin timeout contra un servicio colgado ==
  a los 3 s: sigue esperando = True   (y seguiria horas)
  con timeout=1: TimeoutError a los 1.0 s

== 6.3 · LA TRAMPA 2: el timeout es por espera, no total ==
  timeout=1, pero la llamada duro 3.0 s y NO fallo (10 bytes)
  Cada byte llega antes de 1 s, asi que el reloj se reinicia cada vez.
  con plazo total: TimeoutError a los 1.2 s (plazo total de 1 s superado)
```

## Leccion 07 — Health check: que conteste TU version

`07_salud/comprobar_salud.py` · codigo de salida `0`

```
== 7.1 · LA TRAMPA: 'el puerto contesta' ==
  t=0.0s  el puerto 53776 acepta conexiones -> 'desplegado'

== 7.2 · LA TRAMPA 2: 'la salud da 200' ==
  t=0.0s  /salud -> 200 {'estado': 'ok', 'version': 'v1'}
  200... de la version VIEJA, que todavia no se ha ido.

== 7.3 · Bien: esperar a que conteste la version que desplegaste ==
  t=0.0s  200 {'estado': 'ok', 'version': 'v1'}
  t=1.1s  503 {'estado': 'arrancando'}
  t=1.4s  503 {'estado': 'arrancando'}
  t=1.7s  503 {'estado': 'arrancando'}
  t=1.9s  503 {'estado': 'arrancando'}
  t=2.2s  200 {'estado': 'ok', 'version': 'v2'}  <- esta si (intento 9)

== 7.4 · Y si nunca llega: el plazo decide, no la paciencia ==
  t=2.2s  200 {'estado': 'ok', 'version': 'v2'}
  t=3.2s  plazo agotado tras 4 intentos
```

## Leccion 08 — Marcha atras

`08_marcha_atras/volver_atras.py` · codigo de salida `0`

```
== 8.1 · LA TRAMPA: desplegar encima ==
  la v2 falla. Volver a la v1... app/codigo.txt = 'v2 (rota)'
  La v1 ya no existe en ningun sitio. Volver atras = volver a construirla.

== 8.2 · Una carpeta por release y un puntero a la actual ==
  releases/ = ['v1', 'v2', 'v3']   ACTUAL -> v3
  la v3 falla -> marcha atras: ACTUAL -> v2 en 0.38 ms

== 8.3 · LA TRAMPA 2: limpiar de mas ==
  conservar 1: queda ['v2', 'v3'] (ACTUAL -> v2)
  Si la v2 tambien falla, ya no hay a donde volver. Conserva 3 o mas.

== 8.4 · LA TRAMPA 3: el codigo vuelve atras. La base de datos, no ==
  la v2 renombro la columna ip -> direccion. Falla. Marcha atras al codigo v1:
  la v1 contra la base nueva: OperationalError: no such column: ip
  Haciendolo en dos pasos (primero AGREGAR la columna, borrar la vieja en otra release):
  la v1 contra la base nueva: [('web-01', '10.0.0.5')]
```

## Leccion 09 — Cerrojo: uno a la vez

`09_cerrojo/uno_a_la_vez.py` · codigo de salida `0`

```
== 9.1 · LA TRAMPA: dos despliegues lanzados a la vez ==
  pid 3044: desplegada la release 42
  pid 17260: desplegada la release 42
  empezamos en 41, se desplegaron 2 -> el contador dice 42
  Los dos leyeron 41. Los dos escribieron 42. Uno se perdio.

== 9.2 · Con cerrojo (os.O_CREAT | os.O_EXCL) ==
  pid 28080: desplegada la release 42
  pid 16500: ya hay un despliegue en curso (pid 28080). Salgo.
  contador: 42   codigos de salida: [0, 75]
  O_EXCL crea el archivo solo si NO existe, en una sola operacion.
  Comprobar con exists() y luego crearlo deja un hueco entre las dos.

== 9.3 · LA TRAMPA 2: el cerrojo huerfano ==
  un despliegue murio hace 3 horas sin borrar su cerrojo.
  pid 27888: ya hay un despliegue en curso (pid 999999). Salgo.
  pid 21448: ya hay un despliegue en curso (pid 999999). Salgo.
  y desde entonces nadie despliega: contador 41, codigos [75, 75]
  cerrojo de hace 3 h > 30 min: lo doy por muerto y lo retiro
  cerrojo tomado por este proceso: True
  El plazo tiene que ser mas largo que el despliegue mas lento que tengas.
```

## Leccion 10 — Configuracion y secretos

`10_secretos/config_y_secretos.py` · codigo de salida `0`

```
== 10.1 · LA TRAMPA: get() con un valor por omision vacio ==
  DESTINO no esta definida -> ruta = /srv/app
  El despliegue no falla: copia en /srv/app, que es de OTRA aplicacion.
  (y si esa ruta acaba en un borrado, borra lo que no era)

== 10.2 · Lo obligatorio se pide, y se piden TODOS de una vez ==
  faltan variables: DESTINO, TOKEN_REGISTRO. No despliego nada.
  Una por una, arreglarias DESTINO, lanzarias, y fallaria por TOKEN_REGISTRO.

== 10.3 · LA TRAMPA 2: el secreto se escapa en el log ==
  log: ejecutando docker login registro.interno --username ci --password ghp_R3aLm3nt3S3cr3t0
  log: ejecutando docker login registro.interno --username ci --password '***'
  Mejor aun: que el secreto no vaya en la linea de comandos (se ve en ps).
  docker login lo acepta por la entrada estandar: --password-stdin.

== 10.4 · LA TRAMPA 3: imprimir el objeto de configuracion ==
  print(config) -> ConfigMal(entorno='produccion', token='ghp_R3aLm3nt3S3cr3t0')
  con repr=False -> Config(entorno='produccion')
  Un print() de depuracion olvidado acaba en el log del pipeline, que lee todo el equipo.
```

## Leccion 11 — Codigos de salida y logs

`11_salida/codigos_de_salida.py` · codigo de salida `0`

```
== 11.1 · LA TRAMPA: capturar el error y seguir ==
  salida: 'ERROR: el registro no contesta'
  codigo de salida: 0   <- para el pipeline, todo verde
  con sys.exit(1): codigo 1   <- el pipeline se para aqui

== 11.2 · LA TRAMPA 2: los mensajes ensucian el resultado ==
  VERSION=$(python siguiente_version.py) -> 'conectando con el registro...\ncalculando la siguiente version...\nv2.4.1\n'
  con logging         -> stdout 'v2.4.1\n'
                         stderr ['INFO conectando con el registro...', 'INFO calculando la siguiente version...']
  stdout es para el RESULTADO. Lo que se cuenta, a stderr.

== 11.3 · Codigos que significan algo ==
  desplegar.py sin --version -> codigo 2
  desplegar.py: error: the following arguments are required: --version
  Convencion: 0 bien, 1 fallo, 2 lo llamaste mal. argparse ya usa el 2.
  Si distingues 'fallo y volvi atras' de 'fallo y no pude volver',
  el pipeline puede avisar distinto. Documentalo en el --help.
```

## Leccion 12 — Proyecto: desplegar.py

`12_proyecto/escenario.py` · codigo de salida `0`

```
== 1 · Simulacro de la v1 ==
    [dry-run] copiar v1 -> releases/v1
    [dry-run] ACTUAL: None -> v1
    [dry-run] esperar v1 en /salud (plazo 1.5 s)
  -> codigo 0 en 0.1 s   (no existe srv/releases: el simulacro no creo nada)

== 2 · La v1 de verdad ==
    INFO     copiada releases/v1
    INFO     ACTUAL -> v1
    INFO     v1 contesta sana
  -> codigo 0 en 0.1 s   ACTUAL=v1  releases=['v1']

== 3 · La v2 ==
    INFO     copiada releases/v2
    INFO     ACTUAL -> v2
    INFO     v2 contesta sana
  -> codigo 0 en 0.1 s   ACTUAL=v2  releases=['v1', 'v2']

== 4 · La v2 OTRA vez (el pipeline reintento) ==
    INFO     v2 ya es la version actual: sin cambios
  -> codigo 0 en 0.1 s   ACTUAL=v2  releases=['v1', 'v2']

== 5 · La v3, que sale rota ==
    INFO     copiada releases/v3
    INFO     ACTUAL -> v3
    ERROR    v3 no contesta sana en 1.5 s (ultimo: 500)
    INFO     releases/v3 -> releases/v3.fallida
    WARNING  marcha atras: ACTUAL -> v2, y contesta sana
  -> codigo 1 en 1.6 s   ACTUAL=v2  releases=['v1', 'v2', 'v3.fallida']

== 6 · La v4 ==
    INFO     copiada releases/v4
    INFO     ACTUAL -> v4
    INFO     v4 contesta sana
  -> codigo 0 en 0.1 s   ACTUAL=v4  releases=['v1', 'v2', 'v3.fallida', 'v4']

== 7 · La v5 (y la limpieza, que conserva 3) ==
    INFO     copiada releases/v5
    INFO     ACTUAL -> v5
    INFO     v5 contesta sana
    INFO     limpieza: borrada releases/v1
  -> codigo 0 en 0.1 s   ACTUAL=v5  releases=['v2', 'v3.fallida', 'v4', 'v5']

== 8 · Con otro despliegue en curso (su cerrojo esta puesto) ==
    ERROR    hay otro despliegue en curso desde hace 0 s (desplegar.lock)
  -> codigo 75
```
