# SALIDA — curso «Bash para administradores»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-09-22 18:57:58Z`
- bash: `5.3.15(1)-release`
- sistema: `Windows 10`

## Leccion 01 — Comillas: una palabra o cinco

`01_comillas/comillas.sh` · codigo de salida `0`

```
== 1.1 · Un archivo con un espacio en el nombre ==
  ARCHIVO=informe final.log
  sin comillas, bash parte por espacios:
    palabra: <informe>
    palabra: <final.log>
  con comillas, es UNA:
    palabra: <informe final.log>

== 1.2 · LA TRAMPA: en esa carpeta hay mas archivos ==
final.log
informe
informe final.log
  y ahora: rm $ARCHIVO
+ rm informe final.log
  lo que queda:
informe final.log
  Borro 'informe' y 'final.log', que no tenian nada que ver,
  y el que querias borrar sigue ahi.

== 1.3 · Con comillas, una sola palabra ==
+ rm 'informe final.log'
  quedan: 0 archivos

== 1.4 · Y el * que se cuela ==
  PATRON="*"  y en la carpeta hay uno.log dos.log tres.log
+ echo dos.log tres.log uno.log
dos.log tres.log uno.log
+ echo '*'
*
  Sin comillas, bash cambia el * por los nombres ANTES de ejecutar el comando.
  Si eso llega a un rm, borras lo que haya.

== 1.5 · Los dos sitios donde NO hacen falta ==
  dentro de [[ ... ]] no hay partido de palabras
  [ -n $VACIA ]   dice que NO esta vacia   <- mentira
  [ -n "$VACIA" ] dice que si lo esta   <- correcto
  Sin comillas, [ -n $VACIA ] se convierte en [ -n ], y '-n' como texto es no vacio.
  Regla practica: entrecomilla SIEMPRE, menos dentro de [[ ]] y (( )).
```

## Leccion 02 — set -euo pipefail: lo que arregla y lo que no

`02_modo_estricto/modo_estricto.sh` · codigo de salida `0`

```
== 2.1 · Sin modo estricto: el script no se entera de nada ==
  cp: cannot stat '/no/existe/app.tar.gz': No such file or directory
    desplegando ...
    listo
  codigo de salida: 0   <- CERO. Todo bien, dice.

== 2.2 · Con set -euo pipefail ==
  cp: cannot stat '/no/existe/app.tar.gz': No such file or directory
  codigo de salida: 1
  -e se para en el primer fallo · -u revienta con una variable sin definir

== 2.3 · Que arregla pipefail ==
  cat: /no/existe: No such file or directory
  0
    la tuberia dijo que todo bien
  El estado de una tuberia es el del ULTIMO comando. El error del cat se pierde.
  cat: /no/existe: No such file or directory
  0
  con pipefail, codigo 1

== 2.4 · LA TRAMPA: -e NO salta en todos lados ==
  grep: /etc/hostname: No such file or directory
    1) dentro de un if, el fallo NO para el script
  grep: /etc/hostname: No such file or directory
    2) a la izquierda de || tampoco
    3) y con || true te lo tragas a proposito: resultado=<>
    4) local x=$(...) devuelve 0 (el de 'local', no el del comando)
  set -e ayuda, pero no es una red de seguridad: hay que mirar los codigos.

== 2.5 · La cabecera que se copia en todos los scripts ==
  #!/usr/bin/env bash
  set -euo pipefail
  IFS=$'\n\t'      # separadores: salto de linea y tabulador, no el espacio
```

## Leccion 03 — La variable vacia y rm -rf

`03_rm_rf/variable_vacia.sh` · codigo de salida `0`

```
== 3.1 · La maquina de juguete, antes ==
  .
  ./etc
  ./etc/nginx
  ./etc/nginx/nginx.conf
  ./srv
  ./srv/tienda
  ./srv/tienda/datos
  ./srv/tienda/datos/pedidos.db
  ./srv/tienda/releases
  ./srv/tienda/releases/v3
  ./var
  ./var/log
  ./var/log/app.log

== 3.2 · El script de limpieza de toda la vida ==
  rm -rf "$DIR"/*    <- con la variable puesta hace lo que dice:
  limpiado: /tmp/tmp.cxyPHeK8SE/srv/tienda/releases
  srv
  srv/tienda
  srv/tienda/datos
  srv/tienda/datos/pedidos.db
  srv/tienda/releases

== 3.3 · LA TRAMPA: el dia que llega vacia ==
  (un typo en el nombre, un $1 que no llego, un 'source' que fallo antes)
  lo que el shell IBA a ejecutar (impreso, NO ejecutado):
    rm -rf /*
  Eso no es un error de sintaxis ni da aviso: es un comando valido
  que borra la raiz. El shell no pregunta.

== 3.4 · El mismo fallo, ejecutado de verdad (dentro de la carpeta temporal) ==
  BASE=<carpeta temporal>   SUB=""   ->  rm -rf .//*
  lo que queda de la maquina:
  .
  Se llevo srv, etc y var. En la maquina de verdad, con la ruta absoluta,
  se lleva lo mismo pero empezando por la raiz.

== 3.5 · Tres formas de que no pase ==
  sin argumento:
  limpiar_bien.sh: line 3: 1: falta el directorio a limpiar
  codigo de salida: 1
  con una ruta prohibida:
    me niego a limpiar /
  con la ruta buena:
    limpiado: /tmp/tmp.cxyPHeK8SE/srv/tienda/releases

== 3.6 · Y el otro clasico: el espacio colado ==
  rm -rf "$DIR /viejo"   <- un espacio dentro de las comillas: DOS rutas
  rm -rf "$DIR"/viejo    <- una sola
  Regla: ${DIR:?} en vez de $DIR, y un echo delante hasta que lo veas bien.
```

## Leccion 04 — Codigos de salida y tuberias

`04_codigos/codigos_y_tuberias.sh` · codigo de salida `0`

```
== 4.1 · El estado de una tuberia es el del ULTIMO comando ==
  cat /no/existe | wc -l   ->  codigo 0   <- el del wc, que fue bien
  PIPESTATUS de esa misma tuberia: (1 0)   <- el primero SI fallo

== 4.2 · El clasico: guardar el log con tee ==
  ./desplegar.sh | tee despliegue.log
  codigo: 0   <- el de tee. El 7 del script se perdio.
  con set -o pipefail: 7   <- ahora si

== 4.3 · LA TRAMPA: local se come el codigo ==
  local salida=$(...)  ->  $? = 0
  local y asignacion aparte -> $? = 9
  'local' es un comando, y devuelve SU codigo. Declara primero, asigna despues.

== 4.4 · Comprobar de verdad, comando a comando ==
  [ok]    construir
  [FALLO] publicar (codigo 4)
  [ok]    avisar
  codigo final del script: 0
  Ojo: sin 'exit' en el ultimo paso, el script sale con el codigo del ULTIMO comando.

== 4.5 · Codigos con significado ==
  0   todo bien
  1   fallo generico
  2   lo llamaste mal
  64-78 convencion de sysexits.h (EX_USAGE=64, EX_UNAVAILABLE=69...)
  126 el archivo existe pero no es ejecutable · 127 no existe el comando
  ejemplo real: 127 para un comando que no existe
  130 lo mataste con Ctrl+C (128 + 2, la señal)
```

## Leccion 05 — Comparar: [ ] contra [[ ]]

`05_comparar/comparar.sh` · codigo de salida `0`

```
== 5.1 · Numeros y texto se comparan con operadores distintos ==
  [[ $A -gt $B ]]  ->  10 > 9, correcto
  [[ "$A" > "$B" ]]  ->  FALSO: como texto, '10' va antes que '9'
  -gt -lt -eq -ne para numeros · > < == para texto
  (( A > B ))  ->  correcto, y aqui no hacen falta los dolares

== 5.2 · LA TRAMPA: la variable vacia rompe [ ] ==
  [ $VACIA = "produccion" ]  ->  bash: line 1: [: =: unary operator expected
  (se convierte en [ = "produccion" ], que ni es una comparacion)
  con comillas: compara y dice que no. Bien.
  con [[ ]]: tampoco hace falta comillas. Bien.

== 5.3 · Lo que [[ ]] hace y [ ] no ==
  patron:  [[ $RAMA == feature/* ]]
  regex:   ${BASH_REMATCH[1]} = pago-tarjeta
  && y || dentro: [[ -f x && -r x ]] (en [ ] hay que usar -a, que es peor)
  [ ] es un PROGRAMA (de hecho existe /usr/bin/[). [[ ]] lo interpreta bash.

== 5.4 · Comprobaciones de archivos que se usan a diario ==
  [ -e archivo.txt ]  ->  si
  [ -f archivo.txt ]  ->  si
  [ -d carpeta ]  ->  si
  [ -s archivo.txt ]  ->  no
  [ -r archivo.txt ]  ->  si
  [ -x archivo.txt ]  ->  no
  -e existe · -f es archivo normal · -d directorio · -s no esta vacio · -r legible · -x ejecutable

== 5.5 · Valores por omision, que ahorran la mitad de los if ==
  ${ENTORNO:-produccion}   ->  produccion   (usa el valor si esta)
  ${ENTORNO:=produccion}   ->  produccion   (y ademas lo asigna: ENTORNO=produccion)
  ${TOKEN:?falta el token}  ->  falta el token
  ${RUTA:+--ruta $RUTA}    ->  solo pone el argumento si la variable tiene algo
```

## Leccion 06 — Leer un archivo linea a linea

`06_leer/leer_lineas.sh` · codigo de salida `0`

```
== 6.1 · El archivo ==
  web-01   produccion   Servidor de la tienda <- fin de linea
  web-02   produccion <- fin de linea
  db-01    datos        Base de datos principal <- fin de linea
   <- fin de linea
  cache-01 produccion <- fin de linea

== 6.2 · LA TRAMPA: for linea in $(cat archivo) ==
  vueltas del bucle: 16   <- el archivo tiene 5 lineas
  bash partio por ESPACIOS, no por lineas. Cada palabra es una vuelta.

== 6.3 · while IFS= read -r ==
  1: <web-01   produccion   Servidor de la tienda>
  2: <web-02   produccion>
  3: <db-01    datos        Base de datos principal>
  4: <>
  5: <cache-01 produccion>
  vueltas: 5
  IFS= evita que se coman los espacios · -r que las barras se interpreten

== 6.4 · La ultima linea sin salto: el que se pierde ==
  con 'while read': 2 de 3   <- read devuelve falso en la ultima
  con '|| [[ -n $l ]]': 3 de 3

== 6.5 · LA TRAMPA 2: la tuberia se lleva las variables ==
  despues de 'cat ... | while ...':  total=0   <- se quedo en 0
  La tuberia crea un SUBSHELL: lo que cambies ahi dentro no sale.
  redirigiendo con < :                total=5
  o con sustitucion de proceso < <(...): total=5

== 6.6 · Partir cada linea en campos, sin cortar ==
  web-01     produccion   Servidor de la tienda
  web-02     produccion   (sin descripcion)
  db-01      datos        Base de datos principal
  cache-01   produccion   (sin descripcion)
  El ultimo campo del read se queda con TODO lo que sobra: por eso la descripcion
  con espacios no se parte.
```

## Leccion 07 — Arrays y argumentos

`07_arrays/arrays.sh` · codigo de salida `0`

```
== 7.1 · Una lista de opciones en una variable de texto ==
  OPCIONES="--config /etc/mi app.conf --verbose"   (la ruta tiene un espacio)
  como texto, bash ve 4 palabras:
    <--config>
    </etc/mi>
    <app.conf>
    <--verbose>

== 7.2 · Con un array, cada elemento es un argumento ==
  OPC=(--config "/etc/mi app.conf" --verbose)
  elementos: 3
    <--config>
    </etc/mi app.conf>
    <--verbose>

== 7.3 · LA TRAMPA: ${OPC[@]} sin comillas, y ${OPC[*]} ==
  "${OPC[@]}"  -> cada elemento, UN argumento (lo que quieres casi siempre)
    sin comillas: <--config>
    sin comillas: </etc/mi>
    sin comillas: <app.conf>
    sin comillas: <--verbose>
    con [*]:      <--config /etc/mi app.conf --verbose>   <- todo junto en uno

== 7.4 · Lo mismo con los argumentos del script ==
  recibidos: 4
  con "$@": 
    <--mensaje>
    <todo bien>
    <--destino>
    </tmp>
  con $* (sin comillas):
    <--mensaje>
    <todo>
    <bien>
    <--destino>
    </tmp>

== 7.5 · Construir un comando a trozos, sin eval ==
  comando: tar -czf copia.tar.gz servidores.txt
  hecho: 139 bytes
  Un array se va llenando segun las condiciones y se ejecuta entrecomillado.
  eval con texto es lo que abre la puerta a que un nombre raro ejecute comandos.

== 7.6 · Arrays asociativos (bash 4+) ==
  db -> 5432
  api -> 9000
  web -> 8080
  claves: ${!PUERTO[@]} · valores: ${PUERTO[@]} · y no tienen orden garantizado
```

## Leccion 08 — Expansiones

`08_expansion/expansion.sh` · codigo de salida `0`

```
== 8.1 · El patron que no casa con nada ==
  en una carpeta sin .log:
    <*.log>   <- el patron TAL CUAL, no una lista vacia
  Por eso 'for f in *.log; do rm $f; done' intenta borrar un archivo llamado *.log
  con 'shopt -s nullglob': 0 vueltas

== 8.2 · La sustitucion se come los saltos del final ==
  el archivo acaba con 3 saltos; $(cat) devuelve 13 caracteres:
  <linea1
linea2>
  Comodo casi siempre; te muerde cuando comparas hashes o firmas.

== 8.3 · Recortar rutas sin llamar a basename ==
  $RUTA                 /srv/tienda/releases/v3/app.tar.gz
  ${RUTA##*/}           app.tar.gz          <- el nombre (lo mas largo por delante)
  ${RUTA%/*}            /srv/tienda/releases/v3
  ${RUTA%%.*}           /srv/tienda/releases/v3/app
  ${RUTA##*.}           gz                       <- la extension
  # quita por delante, % por detras · doble = lo mas largo. Y no lanza un proceso.

== 8.4 · Reemplazar y cambiar mayusculas ==
  ${NOMBRE/./_}         web-01_produccion.interno      <- el primero
  ${NOMBRE//./_}        web-01_produccion_interno      <- todos
  ${NOMBRE^^}           WEB-01.PRODUCCION.INTERNO
  ${#NOMBRE}            25

== 8.5 · LA TRAMPA: la virgulilla entre comillas ==
  ~/copias        ->  /c/Users/tu-usuario/copias
  DESTINO="~/copias"  ->  ~/copias   <- no se expandio: es texto
  mkdir "$DESTINO" crea una carpeta que se llama ~ . Usa $HOME.
  DESTINO="$HOME/copias"  ->  /c/Users/tu-usuario/copias

== 8.6 · Llaves: sirven para crear, y para destrozar ==
  mkdir -p copias/{diario,semanal,mensual}  ->  diario mensual semanal 
  echo backup-{1..3}.tar  ->  backup-1.tar backup-2.tar backup-3.tar
  Se expanden ANTES que las variables: con una variable dentro NO funcionan.
  N=3 · echo {1..$N}  ->  1 2 3   (hay que usar eval, o seq)
```

## Leccion 09 — trap y limpieza

`09_trap/trap_y_limpieza.sh` · codigo de salida `0`

```
== 9.1 · LA TRAMPA: el temporal que se queda ==
    trabajando en trabajo.5sxH
  cp: cannot stat '/no/existe/app.tar.gz': No such file or directory
  temporales que han quedado: 1
  Multiplicalo por un cron cada 5 minutos y ahi tienes el disco lleno.

== 9.2 · Con trap EXIT, se limpia pase lo que pase ==
    trabajando en trabajo.5hMb
  cp: cannot stat '/no/existe/app.tar.gz': No such file or directory
    limpieza hecha (codigo 1)
  temporales que han quedado: 0

== 9.3 · El trap tambien salta con una señal ==
  esperando...
  me han matado: limpio y salgo
  (EXIT: la limpieza final siempre pasa por aqui)
  codigo con el que salio: 130
  Sin trap, un TERM deja la maquina a medias: el cerrojo puesto, el temporal lleno.

== 9.4 · trap ERR: enterarte de DONDE fallo ==
    paso 1
    fallo en la linea 5: false

== 9.5 · Los temporales, siempre con mktemp ==
  mal:  TMP=/tmp/copia.$$        <- predecible: otro puede crearlo antes (enlace)
  bien: TMP=$(mktemp -d)          <- nombre al azar, y en Linux permisos 700
  permisos aqui: 755 (esta grabado en Windows;
  en Linux mktemp -d da 700: solo tu entras)
  y el trap EXIT de la primera linea del script, antes de crear nada mas.
```

## Leccion 10 — En paralelo, sin perder los codigos

`10_paralelo/en_paralelo.sh` · codigo de salida `0`

```
== 10.1 · Uno detras de otro ==
  web-01 ok
  web-02 ok
  web-04 ok
  web-05 ok
  web-06 ok
  6 chequeos de 0,4 s en fila: 2675 ms

== 10.2 · LA TRAMPA: & sin wait ==
    todos los chequeos: OK
    web-01 ok
    web-02 ok
  El script dijo OK y se fue. Los procesos hijos seguian corriendo.

== 10.3 · & y wait, recogiendo cada codigo ==
  web-02 ok
  web-01 ok
  web-05 ok
  web-06 ok
  web-04 ok
  CAIDO: web-03
  todos a la vez: 476 ms · caidos: 1
  'wait $pid' devuelve el codigo de ESE proceso. Un 'wait' pelado solo espera.

== 10.4 · Con limite, para no tumbar lo que ibas a medir ==
  con xargs -P 2 (de dos en dos): 1369 ms
  xargs -P N es el semaforo mas corto que hay. Y -I{} evita partir por espacios.
  Ojo: xargs devuelve 123 si algun comando fallo, no el codigo del comando.
  codigo de xargs: 123

== 10.5 · La salida de varios procesos se mezcla ==
  Dos procesos escribiendo a la vez pueden partirse una linea por la mitad.
  Cada uno a su archivo, y se juntan al final:
    salida.web-01.txt:   web-01 ok
    salida.web-02.txt:   web-02 ok
```

## Leccion 11 — #!/bin/sh no es bash

`11_portable/portable.sh` · codigo de salida `0`

```
== 11.1 · Por que el script pasa en tu maquina ==
  El shebang dice #!/bin/sh. Y aqui:
    sh -c 'echo $BASH_VERSION'  ->  5.3.15(1)-release
  En esta maquina (y en muchas) /bin/sh ES bash, asi que el script funciona:
    es una rama de feature
    WEB-01
  En Debian y Ubuntu, /bin/sh es dash. En Alpine, busybox. Ahi NO funciona.

== 11.2 · Lo que no existe en un sh de verdad ==
  [[ ]] · arrays · ${VAR^^} · ${VAR//a/b} · (( )) · local · función() con 'function'
  set -o pipefail · echo -e · read -a · <<< (here-string) · < <(...) · ${!VAR}
  En dash, '[[' se lee como un comando que no existe: 'not found', y el if falla.

== 11.3 · Detectarlos sin tener ese shell delante ==
  una comprobacion casera (grep) sobre bashismos.sh:
  3:if [[ $RAMA == feature/* ]]; then
  6:set -o pipefail
  7:NOMBRES=(web-01 web-02)
  -> 3 lineas sospechosas en bashismos.sh
  Y se deja una: la linea 8, ${NOMBRES[0]^^}, que el grep casero no caza.
  Esa es la lección: un grep hecho a mano siempre se deja algo.
  Lo serio es shellcheck: lee el shebang y avisa de cada bashismo (SC2039/SC3010),
  sin ejecutar nada. Es el primer paso de cualquier pipeline que toque bash.

== 11.4 · El shebang, y lo que cambia entre maquinas aunque uses bash ==
  #!/usr/bin/env bash    <- busca bash en el PATH (mejor que /bin/bash fijo)
  bash de esta maquina: 5.3.15(1)-release
  macOS trae bash 3.2 (de 2007) por licencia: sin arrays asociativos, sin ${VAR^^}
  Y GNU y BSD no comparten opciones: sed -i, readlink -f, stat -c, date -d
  date -d '1 hour ago'  ->  12:58

== 11.5 · La regla ==
  Si el script usa bashismos (y casi todos los usan), el shebang dice bash.
  Si tiene que correr en el contenedor mas pelado que haya, se escribe en POSIX
  y se comprueba: shellcheck -s sh script.sh
```

## Leccion 12 — Proyecto: respaldo.sh

`12_proyecto/escenario.sh` · codigo de salida `0`

```

== 1 · Sin opciones: te dice TODO lo que falta ==
  $ respaldo.sh 
  18:58:37  ERROR: faltan opciones: --origen --destino
  [codigo 2]

== 2 · Con un --conservar que no es un numero ==
  $ respaldo.sh --origen /tmp/tmp.h13Qb4YBKZ/datos de la tienda --destino /tmp/tmp.h13Qb4YBKZ/copias --conservar tres
  18:58:37  ERROR: --conservar tiene que ser un numero: tres
  [codigo 2]

== 3 · Simulacro ==
  $ respaldo.sh --origen /tmp/tmp.h13Qb4YBKZ/datos de la tienda --destino /tmp/tmp.h13Qb4YBKZ/copias --dry-run
  18:58:37  [dry-run] copiaria /tmp/tmp.h13Qb4YBKZ/datos de la tienda -> /tmp/tmp.h13Qb4YBKZ/copias/respaldo-20260922T185837Z.tar.gz
  18:58:37  [dry-run] conservaria las 3 mas recientes
  [codigo 0]
  copias creadas por el simulacro: 0

== 4 · La copia de verdad (el origen lleva espacios en el nombre) ==
  $ respaldo.sh --origen /tmp/tmp.h13Qb4YBKZ/datos de la tienda --destino /tmp/tmp.h13Qb4YBKZ/copias
  18:58:37  copiando /tmp/tmp.h13Qb4YBKZ/datos de la tienda
  18:58:37  hecha: respaldo-20260922T185837Z.tar.gz (1 KB)
  18:58:37  verificada: 7 entradas
  18:58:38  copias que quedan: 1
  [codigo 0]

== 5 · Cuatro copias mas, conservando 3 ==
    18:58:39  hecha: respaldo-20260922T185839Z.tar.gz (1 KB)
    18:58:39  copias que quedan: 2
    18:58:40  hecha: respaldo-20260922T185840Z.tar.gz (1 KB)
    18:58:40  copias que quedan: 3
    18:58:41  hecha: respaldo-20260922T185841Z.tar.gz (1 KB)
    18:58:42  rotacion: borrada respaldo-20260922T185837Z.tar.gz
    18:58:42  copias que quedan: 3
    18:58:43  hecha: respaldo-20260922T185843Z.tar.gz (1 KB)
    18:58:43  rotacion: borrada respaldo-20260922T185839Z.tar.gz
    18:58:43  copias que quedan: 3
  en la carpeta: 3 copias

== 6 · Con otra copia en curso (el cerrojo esta puesto) ==
  18:58:43  ERROR: ya hay una copia en curso (/tmp/tmp.h13Qb4YBKZ/copias/.respaldo.lock)
  [codigo 75]

== 7 · Si el origen no existe (el cron apuntaba a la carpeta vieja) ==
  18:58:43  ERROR: el origen no es un directorio: /tmp/tmp.h13Qb4YBKZ/no-existe
  [codigo 2]
  temporales y cerrojos que han quedado: 0
```
