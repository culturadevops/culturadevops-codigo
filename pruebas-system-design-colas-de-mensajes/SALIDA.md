# SALIDA — «System design: colas de mensajes» (cultura-devops, vídeo 350)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 16:57:54Z`
- RabbitMQ 4.1.4 · cliente Python 3.13 + pika 1.3.2
- 1.000 mensajes por prueba; el consumidor «se cae» con os._exit justo después de procesar el 300 y antes de confirmarlo.
- una sola máquina.

```
== 1 · Confirmación automática (auto-ack) y un consumidor que se cae ==
$ python lab.py autoack   # auto_ack=True
  consumidor 1: se cae tras procesar el mensaje 300, antes de confirmarlo
  consumidor 2: arranca y vacía la cola
  publicados 1000 · procesados 300 · distintos 300 · duplicados 0 · perdidos 700 · quedan en la cola 0

== 2 · Confirmación manual (ack después de procesar) ==
$ python lab.py ack1   # un ack por mensaje
  consumidor 1: se cae tras procesar el mensaje 300, antes de confirmarlo
  consumidor 2: arranca y vacía la cola
  publicados 1000 · procesados 1001 · distintos 1000 · duplicados 1 · perdidos 0 · quedan en la cola 0
$ python lab.py ack50   # un ack cada 50 mensajes
  consumidor 1: se cae tras procesar el mensaje 300, antes de confirmarlo
  consumidor 2: arranca y vacía la cola
  publicados 1000 · procesados 1050 · distintos 1000 · duplicados 50 · perdidos 0 · quedan en la cola 0

== 3 · Consumidor idempotente (recuerda lo que ya hizo) ==
$ python lab.py idempotente   # un ack cada 50, y salta lo que ya está hecho
  consumidor 1: se cae tras procesar el mensaje 300, antes de confirmarlo
  consumidor 2: arranca y vacía la cola
  publicados 1000 · procesados 1000 · distintos 1000 · duplicados 0 · perdidos 0 · quedan en la cola 0

== 4 · El mensaje veneno: falla siempre y se devuelve a la cola ==
$ python lab.py veneno-clasica   # cola clásica, nack con requeue
  en 5 s: 99 buenos confirmados · el veneno se entregó 27343 veces · quedan en la cola 1
$ python lab.py veneno-quorum   # cola quorum, sin configurar nada
  en 5 s: 99 buenos confirmados · el veneno se entregó 21 veces · quedan en la cola 0
$ python lab.py veneno-quorum-dlq   # cola quorum, x-delivery-limit 3 y cola de mensajes muertos
  en 5 s: 99 buenos confirmados · el veneno se entregó 4 veces · quedan en la cola 0
  cola cobros-muertos: 0 más · leído: b'veneno'
  x-death: reason=delivery_limit queue=cobros-quorum-dlq count=1 x-delivery-count=None

== 5 · El orden: 200 pedidos × (creado, pagado, enviado) ==
$ python lab.py orden-dos   # una cola, dos consumidores
  pedidos: 200 · procesados fuera de orden: 119 · c1 hizo 315 · c2 hizo 285
  ejemplo, pedido p4: pagado → enviado → creado
$ python lab.py orden-unico   # una cola con x-single-active-consumer
  pedidos: 200 · procesados fuera de orden: 0 · c1 hizo 600
$ python lab.py orden-particion   # dos colas, el pedido va siempre a la misma
  pedidos: 200 · procesados fuera de orden: 0 · c1 hizo 300 · c2 hizo 300
```
