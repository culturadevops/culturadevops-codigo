# Salida ejecutada — vídeo 219 «Escribí Redis en Python»

> Corrida del 2026-09-07. Servidor: `redis_py.py` en `python:3.12-alpine`, solo biblioteca estándar.
> Cliente: **redis-cli / redis-benchmark 7.4.11 OFICIALES**, de `redis:7-alpine`, por red de Docker.

## La promesa del título: el cliente oficial no nota la diferencia
```
redis-cli 7.4.11

PING            -> PONG
SET saludo hola -> OK
GET saludo      -> hola
EXISTS saludo   -> 1
GET no-existe   -> []  (nil)
INCR visitas    -> 2
INCR visitas    -> 3
DECR visitas    -> 2
SET s v EX 2    -> OK
TTL s           -> 2
(3 s despues)  GET s -> []   TTL s -> -2  (-2 = no existe)
DBSIZE          -> 4
```

## El rendimiento, con `redis-benchmark` oficial

`-t set,get,incr -n 20000 -c 50 -q`

```
SET: 47961.63 requests per second, p50=0.879 msec
GET: 46296.30 requests per second, p50=0.807 msec
INCR: 46189.38 requests per second, p50=0.607 msec
```

### 📊 El número, sin adornos

**Entre 46.000 y 49.000 operaciones por segundo**, según la corrida. Es lo que hay y es lo que
se dice en el vídeo.

⚠️ Y se dice ASÍ, con la horquilla: dos corridas seguidas del mismo banco dieron 48.780/49.019/48.192
y 47.961/46.296/46.189. Dar una sola cifra al decimal sería fingir una precisión que la medida no
tiene. En el vídeo se enseña la corrida que está en este fichero y se dice «unas 47.000».

Como referencia de escala, y nada más: la misma herramienta escrita en Go llegó a unas
**200.000 operaciones por segundo** (medido el 2026-09-05, vídeo 198 de Golandia, mismo
banco de pruebas y mismo cliente oficial). Unas cuatro veces más.

⛔ El vídeo NO se convierte en una comparativa de lenguajes. Se da el dato, se da la escala,
y se sigue: lo que se viene a buscar aquí es terminar con la herramienta en la mano y
habiendo entendido cómo funciona Redis por dentro.
