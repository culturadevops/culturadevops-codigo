# SALIDA — curso «La factura: FinOps para el que paga de su bolsillo»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.** Importes: precio de lista × uso (estimación).

- fecha: `2026-10-05 16:01:50Z` · anfitrión `Windows 10`
- precios: lista de precios pública de AWS, us-east-1 · EC2 2026-09-25 · VPC 2026-09-17 · Lambda 2026-10-01
- `moto 5.2.3 · boto3 1.43.57`
- `OpenTofu v1.12.5`

## Leccion 01 — El plan gratuito ya no es un año: son créditos

`python lecciones/l01_plan_gratuito.py` · codigo de salida `0`

```
== 1.1 · Lo que dice el anuncio (16 de julio de 2025) ==
  «new customers receive $100 in AWS credits upon sign-up and can earn an additional $100 in credits by using services»
  «The free account plan expires either 6 months after sign-up or when Free Tier credits are depleted, whichever comes first»
  «customers continue to have access to over 30 always-free services»

== 1.2 · Lo que se deja encendido, al mes (730 h), a precio de lista ==
  una instancia t3.micro                     7.59 USD
    y su IPv4 pública (también cobra)        3.65 USD
  un disco gp3 de 30 GB                      2.40 USD
  una instantánea de 30 GB                   1.50 USD
  un NAT gateway (sin tráfico)              32.85 USD
    y la IP fija del NAT                     3.65 USD
  TOTAL                                     51.64 USD

== 1.3 · ¿Cuánto duran los créditos? ==
  100 USD de créditos / 51.64 USD al mes = 1.9 meses
  200 USD de créditos / 51.64 USD al mes = 3.9 meses
  solo el NAT con su IP: 36.50 USD al mes, 71% del total

  precios: lista de precios pública de AWS, us-east-1 · EC2 2026-09-25 · VPC 2026-09-17 · Lambda 2026-10-01
```

## Leccion 02 — El presupuesto, por código, y lo que no hace

`python lecciones/l02_presupuesto.py` · codigo de salida `0`

```
== 2.1 · El presupuesto, creado con la API ==
  mi-cuenta: 20 USD · MONTHLY · COST
  aviso: ACTUAL     GREATER_THAN 80 %
  aviso: FORECASTED GREATER_THAN 100 %

== 2.2 · Lo que dice la documentación ==
  «AWS Budgets information is updated up to three times a day. Updates typically occur 8–12 hours after the previous update.»
  «You might incur additional costs or usage that exceed your budget notification threshold before AWS Budgets can notify you»

== 2.3 · Lo que cabe entre dos actualizaciones (hasta 12 h) ==
   1 × m7i.large lanzadas por error, 12 h:   1.21 USD  (6% del presupuesto)
  10 × m7i.large lanzadas por error, 12 h:  12.10 USD  (60% del presupuesto)

  precios: lista de precios pública de AWS, us-east-1 · EC2 2026-09-25 · VPC 2026-09-17 · Lambda 2026-10-01
```

## Leccion 03 — Etiquetar: ¿de quién es este gasto?

`python lecciones/l03_etiquetas.py` · codigo de salida `0`

```
== 3.1 · El coste, por proyecto ==
  tienda             156.07 USD/mes   53.8%
  (sin etiqueta)     121.77 USD/mes   42.0%
  blog                12.04 USD/mes    4.2%
  TOTAL              289.88 USD/mes

== 3.2 · Los que no tienen dueño ==
  instancia    i-97b55c2861b73bee3      t3.micro running                 7.59 USD/mes
  IPv4 pública 54.214.149.175           en uso por i-97b55c2861b73bee3   3.65 USD/mes
  instancia    i-f9ffdaea70a640c52      t3.micro running                 7.59 USD/mes
  IPv4 pública 54.214.246.216           en uso por i-f9ffdaea70a640c52   3.65 USD/mes
  instancia    i-227d0b3e3cb51c562      m7i.large running               73.58 USD/mes
  IPv4 pública 54.214.25.36             en uso por i-227d0b3e3cb51c562   3.65 USD/mes
  disco        vol-8d2fe687a9d3af22d    8 GB gp2, en i-97b55c2861b73be   0.80 USD/mes
  disco        vol-ad23d384255919f73    8 GB gp2, en i-f9ffdaea70a640c   0.80 USD/mes
  disco        vol-2655cd1262ef32fcf    8 GB gp2, en i-227d0b3e3cb51c5   0.80 USD/mes
  disco suelto vol-e0bd4064ea29dfea4    200 GB gp3, sin instancia       16.00 USD/mes
  IPv4 fija    127.233.140.204          SIN USAR                         3.65 USD/mes

== 3.3 · Y la letra pequeña: etiquetar no basta ==
  «For tags to appear on your billing reports, you must activate them.»
  «it can take up to 24 hours for the tag keys to appear on your cost allocation tags page for activation. It can then take up to 24 hours for tag keys to activate.»
```

## Leccion 04 — Lo que sigue cobrando cuando crees que borraste todo

`python lecciones/l04_lo_que_sigue_cobrando.py` · codigo de salida `0`

```
== 4.1 · El entorno de pruebas, encendido ==
  lo que cobra: 7 recursos
    instancia       i-8041730365d01c21d      t3.micro running                     pruebas              7.59 USD/mes
    disco           vol-f1bd631d447646943    8 GB gp2, en i-8041730365d01c21d     (sin etiqueta)       0.80 USD/mes
    disco           vol-c54a34f22e69e2fe9    100 GB gp3, en i-8041730365d01c21d   pruebas              8.00 USD/mes
    instantánea     snap-a5e8b40d8efb3ef72   100 GB de vol-c54a34f22e69e2fe9      (sin etiqueta)       5.00 USD/mes
    IPv4 fija       127.172.145.244          en i-8041730365d01c21d               (sin etiqueta)       3.65 USD/mes
    IPv4 fija       127.8.19.149             en un NAT o interfaz                 (sin etiqueta)       3.65 USD/mes
    NAT gateway     nat-8a376bd5da2d1fe9e    en subnet-4eec21e18587796bd          (sin etiqueta)      32.85 USD/mes
  TOTAL estimado: 61.54 USD al mes (precio de lista, 730 h)

== 4.2 · «Ya terminé»: borro la instancia, como en la consola ==
  la instancia i-8041730365d01c21d: terminated
  lo que SIGUE cobrando: 5 recursos
    disco suelto    vol-c54a34f22e69e2fe9    100 GB gp3, sin instancia            pruebas              8.00 USD/mes
    instantánea     snap-a5e8b40d8efb3ef72   100 GB de vol-c54a34f22e69e2fe9      (sin etiqueta)       5.00 USD/mes
    IPv4 fija       127.172.145.244          SIN USAR (su instancia ya no existe) (sin etiqueta)       3.65 USD/mes
    IPv4 fija       127.8.19.149             en un NAT o interfaz                 (sin etiqueta)       3.65 USD/mes
    NAT gateway     nat-8a376bd5da2d1fe9e    en subnet-4eec21e18587796bd          (sin etiqueta)      32.85 USD/mes
  TOTAL estimado: 53.15 USD al mes (precio de lista, 730 h)
  en un año: 637.80 USD

== 4.3 · Borrar de verdad, en orden: lo que depende de otra cosa, primero ==
  delete_nat_gateway
  release_address × 2
  delete_snapshot
  delete_volume
  lo que cobra ahora: 0 recursos
  TOTAL estimado: 0.00 USD al mes (precio de lista, 730 h)
```

## Leccion 05 — Pagar por hora o por petición

`python lecciones/l05_hora_o_peticion.py` · codigo de salida `0`

```
== 5.1 · Los dos precios ==
  t3.micro + IPv4, todo el mes:             11.24 USD  (pase lo que pase)
  Lambda, 128 MB y 100 ms, por millón:       0.41 USD  (si no hay peticiones, 0)

== 5.2 · Al mes, según el tráfico ==
    peticiones/mes       Lambda     t3.micro  más barato
           100.000     0.04 USD    11.24 USD  Lambda
         1.000.000     0.41 USD    11.24 USD  Lambda
        10.000.000     4.08 USD    11.24 USD  Lambda
        25.000.000    10.21 USD    11.24 USD  Lambda
        50.000.000    20.42 USD    11.24 USD  t3.micro
       100.000.000    40.83 USD    11.24 USD  t3.micro

== 5.3 · El punto de corte ==
  27.5 millones de peticiones al mes = 10.5 peticiones por segundo de media
  el cupo gratuito de Lambda: «The free tier includes one million requests and 400,000 GB-seconds per month.»

  precios: lista de precios pública de AWS, us-east-1 · EC2 2026-09-25 · VPC 2026-09-17 · Lambda 2026-10-01
```

## Leccion 06 — El guion de destrucción, y lo que no destruye

`python lecciones/l06_destruir.py` · codigo de salida `0`

```
== 6.1 · tofu apply: el entorno de pruebas ==
  Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
  lo que cobra (dueño = etiqueta Gestion): 6 recursos
    instancia       i-ee39234b76970b6e8      t3.micro running                     tofu                 7.59 USD/mes
    disco           vol-845ace3bf02841ec0    50 GB gp3, en i-ee39234b76970b6e8    tofu                 4.00 USD/mes
    disco           vol-597a11b714017e34d    8 GB gp2, en i-ee39234b76970b6e8     tofu                 0.80 USD/mes
    IPv4 fija       127.187.202.255          en un NAT o interfaz                 tofu                 3.65 USD/mes
    IPv4 fija       127.188.134.78           en i-ee39234b76970b6e8               tofu                 3.65 USD/mes
    NAT gateway     nat-efc7af3c120cc593e    en subnet-b8446fddab9cdde43          tofu                32.85 USD/mes
  TOTAL estimado: 52.54 USD al mes (precio de lista, 730 h)

== 6.2 · «Una prueba rápida», a mano ==
  aws ec2 create-volume --size 100  -> vol-939be0862813ca33e
  aws ec2 allocate-address          -> 127.73.94.230

== 6.3 · tofu destroy ==
  Destroy complete! Resources: 8 destroyed.
  lo que SIGUE cobrando: 2 recursos
    disco suelto    vol-939be0862813ca33e    100 GB gp3, sin instancia            (sin etiqueta)       8.00 USD/mes
    IPv4 fija       127.73.94.230            SIN USAR                             (sin etiqueta)       3.65 USD/mes
  TOTAL estimado: 11.65 USD al mes (precio de lista, 730 h)
  cazador: código de salida 1 · en un año: 139.80 USD

== 6.4 · Lo que no lleva la marca de tofu: se hizo a mano ==
  disco suelto    vol-939be0862813ca33e    sin «Gestion» -> nadie lo va a destruir con tofu
  IPv4 fija       127.73.94.230            sin «Gestion» -> nadie lo va a destruir con tofu
```

