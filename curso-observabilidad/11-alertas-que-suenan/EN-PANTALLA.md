# Alertas que suenan de verdad (y por qué las tuyas se ignoran) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. una regla de alerta entera

```console
- alert: ErroresAltos
  expr: ...porcentaje de fallo... > 5
  for: 2m
  annotations:
    resumen: "Mas del 5% de las peticiones fallan"
```

## 2. las dos, al mismo tiempo

```console
ErroresAltosSinFor   firing    valor 7,9 %
ErroresAltos         pending   valor 7,9 %

# misma condicion, mismo momento,
# dos estados distintos
```

## 3. separar por gravedad

```console
  labels:
    gravedad: critica    -> telefono
    gravedad: aviso      -> chat

# la misma alerta, distinto destino
```
