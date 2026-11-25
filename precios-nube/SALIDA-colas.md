# SALIDA — colas de mensajes en 4 nubes

Generado 2026-10-14 15:08 UTC con `python colas.py`. Mensajes de 1 KB; 3 peticiones por mensaje (enviar, recibir, borrar) salvo Pub/Sub (2 KB de throughput por mensaje).

## Las tarifas

```
AWS SQS        1 M peticiones gratis al mes · estándar 0.40/M · 0.30/M · 0.24/M · FIFO 0.50/M · 0.40/M · 0.35/M   (lista us-east-1 2026-09-11T12:46:07Z)
Azure Bus Std  10.0 USD al mes de base · operaciones: desde 0 M: 0.00/M · desde 13 M: 0.80/M · desde 100 M: 0.50/M · desde 2,500 M: 0.20/M
Azure Bus Basic 0.05/M operaciones, sin base
Azure Storage Queues (v2, LRS) 0.400/M operaciones de escritura · 0.400/M de lectura (las cuentas v1 se retiraron el 13-10-2026)
Google Pub/Sub 40.0 USD por TiB de throughput · 10 GiB gratis al mes · mínimo 1 KB por petición: sí
Oracle Queue   1 M peticiones gratis al mes · después 0.22/M
Pub/Sub, guardar mensajes ya confirmados o instantáneas: 0.27 USD por GiB al mes
```

## 1 millones de mensajes al mes (3 M peticiones · 1.9 GiB en Pub/Sub)

```
AWS SQS estándar, en lotes de 10         0.00 USD/mes
Google Pub/Sub                           0.00 USD/mes
Azure Service Bus Basic                  0.15 USD/mes
Oracle Queue                             0.44 USD/mes
AWS SQS estándar                         0.80 USD/mes
AWS SQS FIFO                             1.00 USD/mes
Azure Storage Queues                     1.20 USD/mes
Azure Service Bus Standard              10.00 USD/mes
```

## 100 millones de mensajes al mes (300 M peticiones · 190.7 GiB en Pub/Sub)

```
Google Pub/Sub                           7.06 USD/mes
AWS SQS estándar, en lotes de 10        11.60 USD/mes
Azure Service Bus Basic                 15.00 USD/mes
Oracle Queue                            65.78 USD/mes
AWS SQS estándar                       119.60 USD/mes
Azure Storage Queues                   120.00 USD/mes
AWS SQS FIFO                           149.50 USD/mes
Azure Service Bus Standard             179.60 USD/mes
```

## 1,000 millones de mensajes al mes (3,000 M peticiones · 1,907.3 GiB en Pub/Sub)

```
Google Pub/Sub                          74.12 USD/mes
AWS SQS estándar, en lotes de 10       119.60 USD/mes
Azure Service Bus Basic                150.00 USD/mes
Oracle Queue                           659.78 USD/mes
AWS SQS estándar                     1,199.60 USD/mes
Azure Storage Queues                 1,200.00 USD/mes
Azure Service Bus Standard           1,379.60 USD/mes
AWS SQS FIFO                         1,499.50 USD/mes
```

## Pub/Sub: el mínimo de 1 KB por petición, y agrupar

```
100 M mensajes de 100 bytes,   1 por petición → se cobran 1.0 KB por petición →     7.06 USD/mes
100 M mensajes de 100 bytes,  10 por petición → se cobran 1.0 KB por petición →     0.35 USD/mes
100 M mensajes de 100 bytes, 100 por petición → se cobran 10.0 KB por petición →     0.35 USD/mes
```

## Mensajes grandes: 10 M mensajes de 256 KB al mes

```
AWS SQS estándar   4 fragmentos de 64 KB → 90 M peticiones →    35.60 USD/mes
Google Pub/Sub     4,882.8 GiB de throughput →   190.34 USD/mes
```

## SQS: 10 trabajadores consultando una cola vacía, 30 días

```
sondeo corto, 10 consultas/s cada uno       259.2 M peticiones →  103.28 USD/mes
sondeo corto, 1 consulta/s cada uno          25.9 M peticiones →    9.97 USD/mes
sondeo largo de 20 s (el máximo)              1.3 M peticiones →    0.12 USD/mes
```

## Pub/Sub: 100 M mensajes de 1 KB entregados a N suscripciones

```
1 suscripción(es) →   190.7 GiB →   7.06 USD/mes
3 suscripción(es) →   381.5 GiB →  14.51 USD/mes
5 suscripción(es) →   572.2 GiB →  21.96 USD/mes
```

## Azure Service Bus: Premium y conexiones del Standard

```
Premium: 0.9275/h por unidad de mensajería → 677.08 USD/mes por unidad (730 h)
Standard, conexiones: desde 0: 0.0 · desde 1,000: 0.03 · desde 100,000: 0.025 · desde 500,000: 0.015 USD por conexión
```
