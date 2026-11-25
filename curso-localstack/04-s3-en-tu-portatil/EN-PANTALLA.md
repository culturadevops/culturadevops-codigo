# S3 en tu portátil con LocalStack: subir, listar y sincronizar — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. crear el bucket y subir

```console
$ aws --profile lab s3 mb s3://mi-web
make_bucket: mi-web

$ aws --profile lab s3 cp index.html s3://mi-web/
upload: index.html to s3://mi-web/index.html
```

## 2. ver lo que hay dentro

```console
$ aws --profile lab s3 ls s3://mi-web/ --human-readable

2026-08-18 15:12:18   15 Bytes foto.jpg
2026-08-18 15:12:18   32 Bytes index.html
```

## 3. sincronizar la carpeta entera

```console
$ aws --profile lab s3 sync ./web s3://mi-web/

upload: web/foto.jpg to s3://mi-web/foto.jpg
upload: web/index.html to s3://mi-web/index.html

$ aws --profile lab s3 sync ./web s3://mi-web/
# nada: ya estaban los dos
```

## 4. se niega igual que el de verdad

```console
$ aws --profile lab s3 rb s3://mi-web

remove_bucket failed: An error occurred
(BucketNotEmpty) ... The bucket you
tried to delete is not empty
```

## 5. dos versiones del mismo archivo

```console
$ aws --profile lab s3api put-bucket-versioning \
$     --bucket mi-web \
$     --versioning-configuration Status=Enabled

$ aws --profile lab s3api list-object-versions \
$     --bucket mi-web --prefix index.html

OhalxWNLr.h5viiWljOybohyUB4LvAGg    3
null                                32
```

## 6. las cuatro protecciones, activadas

```console
$ aws --profile lab s3api get-public-access-block \
$     --bucket mi-web

  "BlockPublicAcls": true,
  "IgnorePublicAcls": true,
  "BlockPublicPolicy": true,
  "RestrictPublicBuckets": true
```

## 7. pidiéndolo sin credenciales

```console
$ curl http://localhost:4566/mi-web/index.html

<h1>hola desde mi portatil</h1>
```

## 8. una URL caducada hace tres segundos

```console
$ URL=$(aws --profile lab s3 presign \
$       s3://mi-web/index.html --expires-in 1)
$ sleep 3
$ curl $URL

v2
```

## 9. con la firma manipulada a mano

```console
$ curl "${URL%??}zz"
v2

$ # y sin firma ninguna:
$ curl http://localhost:4566/mi-web/index.html
v2
```

## 10. sí comprueba que exista

```console
$ curl http://localhost:4566/mi-web/no-existe.html

<Error><Code>NoSuchKey</Code>
<Message>The specified key does
not exist.</Message></Error>
```

## 11. subiendo a una ruta con barras

```console
$ aws --profile lab s3 cp estilo.css \
$     s3://mi-web/assets/css/estilo.css

upload: estilo.css to
s3://mi-web/assets/css/estilo.css
```

## 12. lo que hay de verdad

```console
$ aws --profile lab s3api list-objects-v2 \
$     --bucket mi-web --query 'Contents[].Key'

assets/css/estilo.css
foto.jpg
index.html
```

## 13. el listado, dibujado como carpetas

```console
$ aws --profile lab s3 ls s3://mi-web/

                    PRE assets/
2026-08-18 15:12:18   15 foto.jpg
2026-08-18 15:12:34    3 index.html
```

## 14. lo borro y desaparece

```console
$ aws --profile lab s3 rm s3://mi-web/index.html
delete: s3://mi-web/index.html

$ aws --profile lab s3 ls s3://mi-web/
# index.html ya no aparece
```

## 15. pero sigue estando

```console
$ aws --profile lab s3api list-object-versions \
$     --bucket mi-web --prefix index.html

DeleteMarkers:
index.html    IsLatest: True
```

## 16. tu web, servida desde el contenedor

```console
$ aws --profile lab s3 sync ./web s3://mi-web/

$ curl http://localhost:4566/mi-web/index.html

<h1>hola desde mi portatil</h1>
```
