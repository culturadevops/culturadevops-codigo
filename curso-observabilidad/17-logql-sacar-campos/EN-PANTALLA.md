# LogQL: filtrar por campos de dentro del log sin indexarlos — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la línea que quiero filtrar

```console
{"msg": "pedido ok",
 "pais": "ES",
 "total": 121.0}
```

## 2. abriendo el JSON al consultar

```console
{app="tienda"} | json | pais = "FR"
                 ^      ^
                 abre   filtra por
                 la     un campo
                 linea  de dentro
```

## 3. lo que devuelve

```console
3 lineas

11:45:33 {"msg":"pedido ok","pais":"FR",...}
11:45:20 {"msg":"pedido ok","pais":"FR",...}
```

## 4. filtrando por un número

```console
{app="tienda"} | json | total > 121

3 lineas, todas con total 123.0

# ni una de 120 ni de 121
```

## 5. las etiquetas, después de todo eso

```console
$ curl localhost:3100/loki/api/v1/labels

app · nivel · service_name

# pais y total NO estan
```

## 6. descartar antes de abrir

```console
# abre TODAS y luego filtra:
{app="tienda"} | json | pais = "FR"

# descarta primero, abre pocas:
{app="tienda"} |= "FR" | json | pais = "FR"
```
