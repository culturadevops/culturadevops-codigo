# Salida ejecutada — vídeo 217 «Escribí SQS en Python»

> Corrida del 2026-09-07. Servidor: `sqs_py.py` en `python:3.12-alpine`, solo biblioteca estándar.
> Cliente: **boto3 OFICIAL**, en otro contenedor, por red de Docker.

```
=== boto3 OFICIAL contra un SQS escrito en Python ===
  boto3 1.43.89

  create_queue -> http://mi-sqs-py:9324/cola/pedidos

--- 1 · RECIBIR NO LO SACA DE LA COLA: LO ESCONDE ---
  send_message  -> ok
  en la cola    -> visibles=1  ocultos=0
  receive       -> pedido-42 · entrega nº 1
  en la cola    -> visibles=0  ocultos=1
     ^ NO se ha borrado. Sigue ahí, escondido.

  otro consumidor pide ahora mismo:
     recibe -> 0 mensajes (no lo ve: está invisible)

--- 2 · SI NO LO BORRAS, VUELVE ---
  el consumidor se muere sin borrar. Esperamos a que pase la invisibilidad...
  receive       -> pedido-42 · entrega nº 2
     ^ EL MISMO MENSAJE, otra vez. Eso es «al menos una vez».
       Tu consumidor tiene que aguantar duplicados. No es opcional.

--- 3 · EL RECIBO CAMBIA EN CADA ENTREGA ---
  recibo de la 1ª entrega: 25450069 ...
  recibo de la 2ª entrega: e05d3469 ...
  ^ por eso no se borra con el MessageId: el recibo demuestra que TÚ
    lo recibiste en ESTA vuelta. Con el id no se sabría de qué entrega hablas.

--- 4 · ahora sí, borrando ---
  delete_message -> ok
  en la cola     -> visibles=0  ocultos=0
  y 6 s después  -> visibles=0  ocultos=0
     ^ ahora sí desapareció. Borrar es lo único que lo saca.
```

### 🥇 Lo que sostiene el vídeo 217

**Recibir un mensaje no lo saca de la cola. Lo esconde.** Se ve en los contadores: tras el
`receive`, `visibles=0 ocultos=1`. No se ha borrado nada. Y otro consumidor pidiendo en ese
momento recibe **0 mensajes**, porque el mensaje está invisible, no ausente.

**Y si no lo borras, vuelve.** Pasada la invisibilidad, el mismo mensaje reaparece como
**entrega nº 2**. Eso es «al menos una vez», y por eso tu consumidor tiene que aguantar
duplicados: no es una recomendación, es cómo funciona.

**El recibo cambia en cada entrega.** Por eso no se borra con el `MessageId`: el recibo demuestra
que TÚ lo recibiste en ESTA vuelta. Con el id no se sabría de qué entrega estás hablando.

### 💡 Por qué escribirlo lo hace evidente

Al implementarlo descubres que **no puedes borrar al entregar**, porque en ese momento no sabes
si el consumidor va a terminar. De esa única imposibilidad salen las tres cosas que la gente
sufre sin entender: el tiempo de invisibilidad, el borrado explícito, y los duplicados.

No hay dos listas ni una «cola de en vuelo». Un mensaje entregado sigue en la misma lista, solo
que con una fecha hasta la que nadie más lo puede ver.
