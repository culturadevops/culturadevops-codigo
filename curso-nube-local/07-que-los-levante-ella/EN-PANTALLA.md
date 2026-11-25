# El escalado de Lambda cabe en tres líneas, y la API de Docker es HTTP (7/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. arrancar el lanzador

```console
$ docker run -d --name nubecita --network demo \
$   -v /var/run/docker.sock:/var/run/docker.sock \
$   nubecita:curso -escuchar 0.0.0.0 \
$   -docker /var/run/docker.sock -red demo \
$   -yo nubecita:4566 -max 3 -ocioso 30s
```

## 2. el fallo, y la ruta que nadie escribio

```console
no puedo levantar un runtime para saludar:
dial unix C:/Program Files/Git/var/run/docker.sock:
connect: no such file or directory
```

## 3. crear la funcion · salida real

```console
$ aws ... lambda create-function --function-name saludar2 \
$    --package-type Image --code ImageUri=funcion-saludar:1 \
$    --timeout 20 --role arn:aws:iam::000000000000:role/x
saludar2   Image   Active
```

## 4. 1a invocacion · salida real, con time

```console
$ time aws ... lambda invoke --function-name saludar2 ...
real    0m0.487s
{"saludo":"hola, Ada","frio":true,
 "invocacion":1,"contenedor":"7ff14abda72e"}
```

## 5. 2a invocacion · salida real, con time

```console
$ time aws ... lambda invoke --function-name saludar2 ...
real    0m0.312s
{"saludo":"hola, Ada","frio":false,
 "invocacion":2,"contenedor":"7ff14abda72e"}
```

## 6. la regla ENTERA del escalado

```console
si no hay NINGUN runtime esperando trabajo
        -> levanta otro
si ya hay uno libre
        -> no hagas nada
si llevas un rato sin que te invoquen
        -> apagalos
```

## 7. el apagado por ocioso · linea real del registro

```console
GET /f/saludar/.../invocation/next
        [el runtime pide trabajo]
-> apagado 83496c8452f6: saludar llevaba
   35s sin invocarse
```

## 8. la API de Docker, tal cual

```console
POST /v1.41/containers/create?name=...
POST /v1.41/containers/{id}/start
POST /v1.41/containers/{id}/stop

sobre /var/run/docker.sock
```

## 9. las cinco lineas, y ya hablas con Docker

```console
&http.Transport{
  DialContext: func(ctx context.Context,
               _, _ string) (net.Conn, error) {
      var d net.Dialer
      return d.DialContext(ctx, "unix", socket)
  },
}
```

## 10. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
frio 0,487 s  ·  templado 0,312 s
corrida: 2026-09-03 · salida-real.txt
```
