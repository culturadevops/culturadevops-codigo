# Cuando reinicias LocalStack, ¿qué se pierde? (y en qué no es AWS) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que había antes de apagar

```console
buckets   : 1
tablas    : pedidos  visitas
funciones : saluda  lenta  rota
            habla  contador
apis      : contador-api
```

## 2. apagar y volver a levantar

```console
$ docker compose down
$ docker compose up -d

buckets   : 0
tablas    : []
funciones : []
apis      : []
```

## 3. qué hay de verdad en esa carpeta

```console
$ ls datos/

cache   lib   logs   tmp

$ du -sh datos/
661K    datos/
```

## 4. la línea que activa la persistencia

```console
    environment:
      - SERVICES=s3,dynamodb,lambda,...
      - DEBUG=0
      - PERSISTENCE=1

# y arranca igual: Ready.
# labaws  Up 12 seconds (healthy)
```

## 5. el resultado, con la persistencia puesta

```console
buckets  : []
tablas   : [sobrevive]
funciones: []

$ # y el dato de la tabla:
hola
```

## 6. al quitar la variable otra vez

```console
$ # quito PERSISTENCE del compose
$ docker compose down && docker compose up -d

$ aws --profile lab dynamodb list-tables
[]

# la tabla que sobrevivio ya no esta
```

## 7. empieza por limpiar

```console
# borra lo anterior y no te quejes
aws $L s3 rb s3://mi-web --force \
  >/dev/null 2>&1 || true
aws $L dynamodb delete-table \
  --table-name pedidos \
  >/dev/null 2>&1 || true
```

## 8. que termine comprobándose

```console
# la ultima linea del script:
curl -s $URL

{"visitas": 1, "ruta": "/"}

# si sale esto, todo esta en pie
```
