# SALIDA — curso «Un incidente de principio a fin: romperlo, diagnosticarlo y el postmortem»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.** Los postmortems están en `postmortems/`.

- fecha: `2026-10-05 15:36:04Z` · anfitrión `Windows 10`
- tiempos comprimidos: Prometheus mide y evalúa cada 5 s; las alertas piden 10-15 s
- `grafana/loki:3.3.2`
- `nginx:1.27-alpine`
- `postgres:17`
- `prom/alertmanager:v0.28.0`
- `prom/blackbox-exporter:v0.25.0`
- `prom/prometheus:v3.1.0`
- `python:3.13-slim`

## Incidente 1 — Se llenó el disco, y lo que falló fue otra cosa

`python incidentes/i1_disco_lleno.py` · codigo de salida `0`

```
== 1.1 · Un martes normal ==
  [   8.0 s] tráfico normal · 200: 116
  [   8.0 s] alguien activa el modo depuración (y se olvida)

== 1.2 · Salta la alerta ==
  [  41.7 s] ALERTA ErroresAltos: «Más del 5% de las peticiones fallan»
  tráfico desde el principio: 200: 157, 500: 447

== 1.3 · Diagnóstico: ¿qué falla? ==
  PromQL  /pedido  200:  0.00 por segundo
  PromQL  /pedido  500: 14.12 por segundo
  [  42.6 s] las métricas: solo falla /pedido, con 500

== 1.4 · Diagnóstico: ¿por qué? Los registros ==
  LogQL   15:36:49Z  {"msg": "no se pudo auditar el pedido", "instancia": "tienda", "error": "[Errno 28] No space left on device"}
  LogQL   15:36:49Z  {"msg": "no se pudo auditar el pedido", "instancia": "tienda", "error": "[Errno 28] No space left on device"}
  [  42.6 s] los registros: «No space left on device»

== 1.5 · ¿Qué llenó el disco? Y el cambio reciente ==
  tmpfs           2.0M  2.0M     0 100% /datos
  -rw-r--r-- 1 root root 2097152 Oct  5 15:36 auditoria.log
  LogQL   15:36:14Z  {"msg": "modo depuracion ACTIVADO", "instancia": "tienda", "por": "ana"}
  [  42.9 s] causa: el modo depuración, activado hace unos minutos

== 1.6 · Mitigar: apagar la depuración y vaciar el fichero ==
  [  53.5 s] MITIGADO: tienda reiniciada (depuración apagada) y auditoría vaciada
  tmpfs           2.0M  4.0K  2.0M   1% /datos
  [  81.7 s] la alerta se resuelve sola
  tráfico total del incidente: 200: 556, 500: 593, RemoteDisconnected: 2

== 1.7 · El postmortem ==
  -> postmortem escrito: postmortems/01.md (detección 34 s · mitigación 45 s)
```

## Incidente 2 — Una fuga de memoria que tarda días

`python incidentes/i2_fuga_de_memoria.py` · codigo de salida `0`

```
== 2.1 · Se despliega la versión con la caché ==
  [  11.2 s] desplegada la versión con caché (FUGA=1) · límite del contenedor: 160 MiB, sin swap

== 2.2 · La alerta predictiva: antes de que se acabe ==
  [  44.6 s] ALERTA MemoriaSeAgota: «al ritmo actual, se acaba en menos de 2 minutos»
  memoria en ese momento: 79 MiB de 160

== 2.3 · Nadie hace caso, y el núcleo la mata ==
  [  93.6 s] la tienda muere y Docker la levanta (reinicios: 1)
  docker events: oom
  docker events: die 137
  tráfico hasta aquí: 200: 797, ConnectionAbortedError: 1, RemoteDisconnected: 3

== 2.4 · El diente de sierra: la memoria cada 5 s, en MiB ==
  23 25 34 43 52 61 70 79 88 97 106 115 124 133 141 150 159 168 29 38 47 56 65

== 2.5 · Mitigar: la caché con un tope de 100 entradas ==
  [ 133.1 s] MITIGADO: desplegada la caché con tope (CACHE_MAX=100)
  memoria cada 5 s: 74 30 40 43 43 43 43 44 46 48 56 45 49 45 47 47 45 47 47 MiB
  tráfico: 200: 847 · reinicios: 0
  [ 223.2 s] 90 s con el mismo tráfico: la memoria se queda plana y no hay reinicios

== 2.6 · El postmortem ==
  -> postmortem escrito: postmortems/02.md (detección 33 s · mitigación 122 s)
```

## Incidente 3 — El certificado que caducó un domingo

`python incidentes/i3_certificado.py` · codigo de salida `0`

```
== 3.1 · La web funciona. Y le quedan 3 días ==
  sonda: probe_success 1
  PromQL: días que le quedan = 3.0
  [   7.5 s] ALERTA CertificadoCaducaPronto: «caduca en menos de 14 días» (y nadie la atiende)

== 3.2 · Llega el domingo ==
  [  12.8 s] el certificado caduca
  un cliente: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1032)
  [  32.5 s] ALERTA CertificadoFalla: «la comprobación HTTPS falla»

== 3.3 · Diagnóstico ==
  sonda: probe_success 0  · Error for HTTP request" err="Get \"https://192.168.16.8\": tls: failed to verify certificate: x509: certificate has expired or is not yet valid: current time 2026-10-05T15:41:49Z is after 2026-10-05T14:41:12Z
  openssl x509 -enddate: notAfter=Oct  5 14:41:12 2026 GMT
  [  34.1 s] diagnóstico: el certificado servido está caducado

== 3.4 · Mitigar: el certificado renovado ==
  [  34.6 s] MITIGADO: certificado renovado (90 días) y nginx recargado
  sonda: probe_success 1
  PromQL: días que le quedan = 90.0
  [  42.5 s] la alerta CertificadoFalla se resuelve

== 3.5 · El postmortem ==
  -> postmortem escrito: postmortems/03.md (detección 20 s · mitigación 22 s)
```

## Incidente 4 — El despliegue que perdió peticiones a medias

`python incidentes/i4_despliegue.py` · codigo de salida `0`

```
== 4.1 · Un despliegue por turnos, como en los tutoriales ==
  [   4.0 s] tráfico de pagos (1 s cada uno) · 200: 24
  [  15.3 s] tienda-a: parada y recreada en 10.5 s · el balanceador ya le manda tráfico
  [  27.0 s] tienda-b: parada y recreada en 10.5 s · el balanceador ya le manda tráfico
  [  32.0 s] despliegue terminado · 200: 234, 502: 6
  pagos fallidos durante el despliegue: 6

== 4.2 · ¿Por qué tarda tanto en pararse? Lo que hace docker stop ==
  docker stop tienda-a: 10.2 s · código de salida 137

== 4.3 · Lo correcto: atender SIGTERM, terminar lo que hay a medias, y un balanceador que reintenta ==
  [   4.0 s] tráfico de pagos (1 s cada uno) · 200: 24
  [   8.5 s] tienda-a: parada y recreada en 0.5 s · el balanceador ya le manda tráfico
  [  12.4 s] tienda-b: parada y recreada en 1.4 s · el balanceador ya le manda tráfico
  [  17.1 s] despliegue terminado · 200: 128
  pagos fallidos durante el despliegue: 0
  [  17.1 s] MITIGADO: apagado limpio + reintento en el balanceador
  docker stop tienda-a: 0.5 s · código de salida 0

== 4.4 · El postmortem ==
  -> postmortem escrito: postmortems/04.md
```

## Incidente 5 — La consulta lenta que solo lo es en producción

`python incidentes/i5_consulta_lenta.py` · codigo de salida `0`

```
== 5.1 · En pruebas: mil pedidos ==
  1000 pedidos · media del historial: 5 ms · 200: 1352

== 5.2 · En producción: tres millones (y un Postgres con media CPU) ==
  [  49.1 s] producción: 3000000 pedidos, el mismo código
  [  88.4 s] ALERTA HistorialLento: «el historial tarda de media más de 300 ms»
  media del historial: 804 ms · 200: 174

== 5.3 · Diagnóstico: ¿qué consulta? pg_stat_statements ==
  181 llamadas · media 666 ms · SELECT id, total FROM pedidos WHERE cliente = $1 ORDER BY creado DESC
  [  90.2 s] la consulta más lenta: el historial

== 5.4 · Diagnóstico: ¿por qué? EXPLAIN ANALYZE ==
  Limit (actual time=698.584..801.629 rows=10 loops=1)
    ->  Gather Merge (actual time=698.581..801.624 rows=10 loops=1)
          Workers Planned: 2
          Workers Launched: 2
          ->  Sort (actual time=631.105..631.107 rows=9 loops=3)
                Sort Key: creado DESC
                Sort Method: top-N heapsort  Memory: 26kB
                Worker 0:  Sort Method: quicksort  Memory: 25kB
                Worker 1:  Sort Method: quicksort  Memory: 25kB
                ->  Parallel Seq Scan on pedidos (actual time=66.602..631.007 rows=17 loops=3)
                      Filter: (cliente = 42)
                      Rows Removed by Filter: 999983
  Planning Time: 0.563 ms
  Execution Time: 801.729 ms
  [  92.0 s] causa: lee la tabla entera (no hay índice por cliente)

== 5.5 · Mitigar: un índice, creado sin bloquear la tabla ==
  [ 135.2 s] MITIGADO: índice creado con CONCURRENTLY en 43.2 s, sin cortar el tráfico
  Limit (actual time=0.013..0.031 rows=10 loops=1)
    ->  Index Scan using pedidos_cliente_creado on pedidos (actual time=0.012..0.030 rows=10 loops=1)
          Index Cond: (cliente = 42)
  Planning Time: 0.159 ms
  Execution Time: 0.053 ms
  [ 148.4 s] la alerta se resuelve
  media del historial: 5 ms · 200: 1839

== 5.6 · El postmortem ==
  -> postmortem escrito: postmortems/05.md (detección 39 s · mitigación 86 s)
```

