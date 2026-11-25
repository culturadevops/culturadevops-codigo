# Loki NO indexa tus logs (y por eso es barato) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. el índice entero de Loki

```console
$ curl localhost:3100/loki/api/v1/labels

app           -> tienda
nivel         -> error, info
service_name  -> tienda
```

## 2. las dos partes de una consulta

```console
{app="tienda", nivel="error"}
        ^ obligatorio: el indice

{app="tienda"} |= "sin tarifa"
               ^ opcional: el texto
```

## 3. buscar solo por texto

```console
|= "sin tarifa"

HTTP 400
parse error at line 0, col 1:
syntax error: unexpected |=
```

## 4. lo que tarda cada una

```console
{app="tienda", nivel="error"}
   94 lineas en 0,015 s

{app="tienda"} |= "sin tarifa"
   94 lineas en 0,017 s
```
