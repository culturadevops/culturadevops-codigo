# SALIDA — curso «Restaurar, no copiar: copias de seguridad que de verdad funcionan»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-10-05 14:22:08Z`
- servidor: `postgres (PostgreSQL) 17.11 (Debian 17.11-1.pgdg13+2)` (imagen `postgres:17`, WAL archivado)
- Docker `29.6.2` · age `1.2.1` · `git version 2.47.3`
- anfitrión: `Windows 10`

## Leccion 01 — La copia que vale 20 bytes

`bash lecciones/01_la_copia_vacia.sh   # dentro del operador` · codigo de salida `0`

```
== 1.1 · La copia de siempre, desde tu terminal ==
  código de salida: 0 · tamaño: 7137 bytes

== 1.2 · La misma línea, desde cron (entorno vacío: sin PGPASSWORD) ==
Password: 
  pg_dump: error: connection to server at "db" (192.168.16.2), port 5432 failed: fe_sendauth: no password supplied
  código de salida: 0
  tamaño: 20 bytes
  gzip -t: el fichero está «bien» (es un gzip válido... de nada)

== 1.3 · El día que hace falta: restaurar la copia de cron ==
  psql: código de salida 0 · pedidos restaurados: -

== 1.4 · Lo correcto: set -o pipefail, y comprobar que la copia tiene algo ==
  con pipefail -> código de salida: 1
  terminal.sql.gz: 7137 bytes -> ok
  cron.sql.gz: 20 bytes < 1024 -> ALARMA: la copia está vacía
```

## Leccion 02 — El ensayo cronometrado: RPO y RTO

`bash lecciones/02_ensayo_cronometrado.sh   # dentro del operador` · codigo de salida `0`

```
== 2.1 · Lo que se pierde: una tienda que vende mientras se hace la copia ==
  copia hecha · la tienda sigue vendiendo 5 segundos más
  pedidos justo antes del desastre: 1059
  pedidos en la copia restaurada:   1017
  perdidos: 42, los de los últimos 5 segundos

== 2.2 · Lo que se tarda: restaurar según el tamaño ==
  pedidos           copia    restaurar
  10000              57 KB        51 ms
  100000            539 KB       250 ms
  1000000          5351 KB      1694 ms

== 2.3 · El millón, restaurado con 4 procesos (pg_restore -j 4) ==
  1000000 pedidos con -j 4: 1614 ms · pedidos: 1000000
```

## Leccion 03 — Lo que pg_dump no lleva: los roles

`bash lecciones/03_lo_que_no_viaja.sh   # dentro del operador` · codigo de salida `0`

```
== 3.1 · Restaurar la copia en un servidor nuevo, como siempre ==
  psql:/copias/tienda.sql:38: ERROR:  role "app" does not exist
  psql:/copias/tienda.sql:52: ERROR:  role "app" does not exist
  psql: código de salida 0
  pedidos restaurados: 1000
  dueño de la tabla: admin
  rol app: NO EXISTE

== 3.2 · Lo mismo con ON_ERROR_STOP: el primer error para todo ==
  psql:/copias/tienda.sql:38: ERROR:  role "app" does not exist
  psql: código de salida 3

== 3.3 · Lo correcto: copiar también los roles (pg_dumpall --globals-only) ==
  roles en la copia: 2
  psql:/copias/roles.sql:16: ERROR:  role "admin" already exists
  rol app: existe
  psql: código de salida 0
  dueño de la tabla: app
```

## Leccion 04 — Volver a un segundo concreto: punto en el tiempo

`bash lecciones/04_punto_en_el_tiempo.sh   # dentro del operador` · codigo de salida `0`

```
== 4.1 · La copia base, y la tienda sigue vendiendo ==
  copia base hecha con 1000 pedidos
  2026-10-05 14:22:46.032328+00 -> todo bien, 1300 pedidos

== 4.2 · El desastre: un DELETE sin WHERE, y la tienda no se entera ==
  2026-10-05 14:22:47.093583+00 -> DELETE FROM pedidos;  quedan 0

== 4.3 · Restaurar la copia de la noche ==
  pedidos: 1000 de 1300 -> se pierden 300

== 4.4 · Restaurar hasta el segundo anterior al DELETE ==
  pedidos: 1300 de 1300 -> se pierden 0 · tardó 1531 ms
  (y los 100 vendidos DESPUÉS del DELETE tampoco están: esos hay que rescatarlos aparte)
  log: starting point-in-time recovery to 2026-10-05 14:22:46.032328+00
  log: recovery stopping before commit of transaction 894, time 2026-10-05 14:22:47.074641+00

== 4.5 · La trampa: el archivado que falla en silencio ==
  pg_stat_archiver: fallos 0 -> 3 · último archivado: 000000010000000000000028 · último fallido: 000000010000000000000029
  y la tienda: sigue vendiendo, 200 pedidos, ni un error
```

## Leccion 05 — Los volúmenes de Docker

`sh lecciones/05_volumenes.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
  la aplicación tiene 1000 pedidos

== 5.1 · La trampa: «copio el contenedor» con docker commit ==
  docker commit: hecho, imagen curso-vol-imagen
  (el desastre: se pierden el contenedor y su volumen)
  levantado desde la imagen copiada -> pedidos: ERROR:  relation "pedidos" does not exist
  la imagen declara el volumen /var/lib/postgresql/data: su contenido no viaja en ella

== 5.2 · La otra trampa: docker compose down -v ==
  volúmenes antes:  curso-vol-demo_datos 
  tras «down»:      curso-vol-demo_datos 
  tras «down -v»:   (ninguno, y sin preguntar)

== 5.3 · Lo correcto: copiar el volumen, con la base de datos parada ==
  copia del volumen: 6377 KB · servicio parado: 1300 ms
  (el mismo desastre)
  levantado desde la copia del volumen -> pedidos: 1000
```

## Leccion 06 — El repositorio: lo que no viaja en un clon

`bash lecciones/06_git.sh   # dentro del operador` · codigo de salida `0`

```
== 6.1 · El portátil de hoy ==
  rama arreglo-urgente (sin subir)   sí
  stash (el experimento)             sí
  etiqueta v1.4-candidata            sí
  .env (ignorado por git)            sí
  hook pre-commit                    sí

== 6.2 · El portátil se muere. Lo normal: git clone ==
  git clone: código de salida 0
  rama arreglo-urgente (sin subir)   NO
  stash (el experimento)             NO
  etiqueta v1.4-candidata            NO
  .env (ignorado por git)            NO
  hook pre-commit                    NO

== 6.3 · Lo correcto: git bundle --all + los ficheros ignorados y los hooks ==
  copias: trabajo.bundle 1113 bytes · ignorados.tgz 9522 bytes
  rama arreglo-urgente (sin subir)   sí
  stash (el experimento)             solo el último (stash list sale vacío)
  etiqueta v1.4-candidata            sí
  .env (ignorado por git)            sí
  hook pre-commit                    sí
```

## Leccion 07 — Los secretos: la clave que estaba en la máquina

`bash lecciones/07_secretos.sh   # dentro del operador` · codigo de salida `0`

```
== 7.1 · Una copia cifrada, como debe ser ==
  Public key: age1khqmyj5rycfq05re59v8t4eq5tu2p45vwxsx536unnguefljaezscnj6et
  código de salida: 0 · 8764 bytes · empieza por: age-encryption.org/v1

== 7.2 · La máquina se muere. Restaurar con lo que queda ==
  ¿la copia está? sí · ¿la clave? NO
  age -d: código de salida 1 · age: error: reading "/root/.clave-copias": failed to open file: open /root/.clave-copias: no such file or directory
  con una clave nueva: age: error: no identity matched any of the recipients

== 7.3 · Lo correcto: la clave apartada, y el ensayo la usa ==
  código de salida: 0 · pedidos restaurados: 1000
  ⚠️ «apartada» quiere decir otro sitio: un gestor de contraseñas, un sobre, otra cuenta.
     Junto a las copias, como aquí por comodidad, cualquiera que robe las copias las abre.
```

## Leccion 08 — La retención que se come la última copia buena

`bash lecciones/08_retencion.sh   # dentro del operador` · codigo de salida `0`

```
== 8.1 · El cajón de copias, antes de la retención ==
  09-21     7138 bytes  tienda-09-21.sql.gz
  09-22     7138 bytes  tienda-09-22.sql.gz
  09-23     7138 bytes  tienda-09-23.sql.gz
  09-24     7138 bytes  tienda-09-24.sql.gz
  09-25     7138 bytes  tienda-09-25.sql.gz
  09-26     7138 bytes  tienda-09-26.sql.gz
  09-27     7138 bytes  tienda-09-27.sql.gz
  09-28       20 bytes  tienda-09-28.sql.gz
  09-29       20 bytes  tienda-09-29.sql.gz
  09-30       20 bytes  tienda-09-30.sql.gz
  10-01       20 bytes  tienda-10-01.sql.gz
  10-02       20 bytes  tienda-10-02.sql.gz
  10-03       20 bytes  tienda-10-03.sql.gz
  10-04       20 bytes  tienda-10-04.sql.gz
  14 copias · buenas: 7 · vacías: 7

== 8.2 · La retención de siempre: find -mtime +7 -delete ==
  código de salida: 0
  7 copias · buenas: 0 · vacías: 7

== 8.3 · Lo correcto: guardar las últimas N BUENAS, y avisar si la más nueva es vieja ==
  14 copias · buenas: 7 · vacías: 7
  la copia buena más nueva: tienda-09-27.sql.gz, de hace 203 horas
  ALARMA: la última copia buena tiene más de 26 horas: las copias están fallando
```

## Leccion 09 — El proyecto: ensayo.sh

`bash lecciones/09_proyecto.sh   # dentro del operador` · codigo de salida `0`

```
== 9.1 · El ensayo, con la tienda vendiendo ==
ensayo de restauración · base de datos «tienda» · 2026-10-05 14:23:17Z
  1 · copia: 11 KB · 2 tablas en la huella
  2 · restaurada en un servidor nuevo en 92 ms
  3 · verificación, tabla por tabla:
      facturas          500 filas  ✓
      pedidos          1001 filas  ✓
  4 · RTO medido: 92 ms · RPO: lo escrito en los últimos 2 s (la edad de la copia)
  RESULTADO: la copia sirve (código 0)
  -> código de salida 0

== 9.2 · La copia que «alguien» aligeró: --exclude-table-data=facturas ==
ensayo de restauración · base de datos «tienda» · 2026-10-05 14:23:19Z
  1 · copia: 8 KB · 2 tablas en la huella
  2 · restaurada en un servidor nuevo en 92 ms
  3 · verificación, tabla por tabla:
      facturas          500 filas en la copia, 0 restauradas  ✗
      pedidos          1029 filas  ✓
  4 · RTO medido: 92 ms · RPO: lo escrito en los últimos 2 s (la edad de la copia)
  RESULTADO: restaura, pero 1 tabla(s) no cuadran (código 1)
  -> código de salida 1

== 9.3 · Una copia dañada ==
ensayo de restauración · base de datos «tienda» · 2026-10-05 14:23:21Z
  1 · copia: 11 KB · 2 tablas en la huella
    (rota a propósito: cortada por la mitad)
  ✗ pg_restore: error: could not read from input file: end of file
  RESULTADO: no hay copia que sirva (código 2)
  -> código de salida 2

== 9.4 · La copia que dejó el cron de la lección 1 ==
ensayo de restauración · base de datos «tienda» · 2026-10-05 14:23:23Z
  ✗ base.dump tiene 20 bytes: está vacía
  RESULTADO: no hay copia que sirva (código 2)
  -> código de salida 2
```

