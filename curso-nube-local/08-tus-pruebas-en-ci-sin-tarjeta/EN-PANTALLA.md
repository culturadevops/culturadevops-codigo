# Pruebas que arrancan siempre del mismo sitio, sin tarjeta (curso 8/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. 1 · para desarrollar: -datos

```console
$ docker run --rm -p 4566:4566 \
$   -v "$PWD/datos:/datos" nubecita:curso \
$   -escuchar 0.0.0.0 -datos /datos/estado.json
lee al arrancar  Y  escribe cuando algo cambia
```

## 2. 2 · para probar: -semilla

```console
$ docker run --rm -p 4566:4566 \
$   -v "$PWD/datos:/datos" nubecita:curso \
$   -escuchar 0.0.0.0 -semilla /datos/semilla.json
lee al arrancar  y  NO escribe NUNCA
```

## 3. el estado ANTES · salida real

```console
$ sha256sum semilla-real.json
de5bca04112fca24
```

## 4. lo que trae puesto · salida real

```console
$ aws ... s3 ls s3://sembrado/
2026-09-03 18:49:11    22 contrato.txt
```

## 5. escribo algo nuevo · salida real

```console
$ aws ... s3 cp h.txt s3://sembrado/h.txt
$ aws ... s3 ls s3://sembrado/
2026-09-03 18:49:11    22 contrato.txt
2026-09-03 18:54:36     5 h.txt
```

## 6. el estado DESPUES · salida real

```console
$ sha256sum semilla-real.json
de5bca04112fca24

-> IDENTICA
```

## 7. lo que pasa si te lo inventas · salida real

```console
no puedo leer /datos/semilla.json:
no es un estado de nubecita:
json: unknown field "s3"
```

## 8. los cuatro pasos, en tu fichero de CI

```console
1. levantar el doble con -semilla
2. exportar AWS_ENDPOINT_URL apuntando a el
3. correr tu suite de siempre
4. tirar el contenedor
```

## 9. esperar bien, no a ojo

```console
hasta 30 intentos:
    si  aws ... s3 ls  contesta  -> sigue
    si no                        -> espera 1 s

y si se agotan los 30, falla con un mensaje claro
```

## 10. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
nubecita:curso   ·  10,5 MB en disco
corrida: 2026-09-03 · salida-real.txt
```
