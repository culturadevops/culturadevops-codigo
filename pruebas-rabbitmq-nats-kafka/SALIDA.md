# SALIDA — RabbitMQ vs NATS vs Kafka (vídeo 342)

Generado 2026-10-08 00:36 UTC con `python correr.py`. RabbitMQ 4, NATS 2.15 (core + JetStream), Kafka 4 (KRaft).

## 1 · Versiones

### versiones

`$ rabbitmqctl / nats-server / kafka`

```
RabbitMQ 4.3.6
NATS v2.15.0
Kafka 4.3.1
```

## 2 · La prueba clave: envío SIN consumidor, y luego llego

### RabbitMQ: publico 10 sin consumidor, luego consumo

`$ pika publish ×10 → basic_get`

```
publicados 10
el consumidor recibió 10 mensajes
```

### NATS (core): publico 10 sin suscriptor, luego me suscribo

`$ nats pub ×10 → timeout 6 nats sub`

```
publicados 10
el consumidor recibió 0 mensajes
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 8 bytes to "pedidos"
00:35:36 Published 9 bytes to "pedidos"
Terminated
```

### NATS (JetStream): con persistencia

`$ nats stream add; pub ×10; stream info`

```
publicados 10 en el stream
guardados → Messages: 10
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 8 bytes to "js.pedidos"
00:35:43 Published 9 bytes to "js.pedidos"
```

### Kafka: produzco 10 sin consumidor, luego leo desde el principio

`$ kafka-console-producer → consumer --from-beginning`

```
publicados 10
el consumidor recibió 10
```

## 3 · Kafka: otro consumidor vuelve a leerlo todo

### un segundo grupo lee desde el principio

`$ kafka-console-consumer --group otro --from-beginning`

```
el 2.º consumidor recibió 10
```

### RabbitMQ: la cola ya está vacía

`$ basic_get otra vez`

```
el consumidor recibió 0 mensajes
```

## 4 · Rendimiento orientativo (herramienta nativa de cada uno)

### NATS: nats bench pub

`$ nats bench pub (100k mensajes de 128 B)`

```
NATS Core NATS publisher stats: 2,918,424 msgs/sec ~ 356 MiB/sec ~ min: 0.04us ~ avg: 0.24us ~ max: 149.89us ~ P50: 0.05us ~ P90: 0.07us ~ P99: 1.24us ~ P99.9: 45.48us
```

### Kafka: kafka-producer-perf-test

`$ 100k mensajes de 128 B`

```
100000 records sent, 122249.388753 records/sec (14.92 MB/sec), 107.41 ms avg latency, 332.00 ms max latency, 88 ms 50th, 204 ms 95th, 205 ms 99th, 206 ms 99.9th.
```

### memoria de cada broker (en reposo)

`$ docker stats --no-stream`

```
rabbit 139.7MiB / 15.36GiB
nats 10.95MiB / 15.36GiB
kafka 345.9MiB / 15.36GiB
```
