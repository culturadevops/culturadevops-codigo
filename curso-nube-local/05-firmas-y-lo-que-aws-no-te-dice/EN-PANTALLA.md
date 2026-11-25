# SignatureDoesNotMatch: por fin alguien te dice por qué (curso 5/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. encender la comprobacion

```console
$ docker run --rm -p 4566:4566 nubecita:curso \
$        -escuchar 0.0.0.0 -firmar
nubecita · ... · comprobando firmas SigV4
```

## 2. la credencial buena · salida real

```console
$ export AWS_SECRET_ACCESS_KEY=prueba
$ aws --endpoint-url ... s3 mb s3://privado2
make_bucket: privado2
```

## 3. la credencial mala · salida real

```console
$ export AWS_SECRET_ACCESS_KEY=me-la-invento
$ aws --endpoint-url ... s3 ls
An error occurred (SignatureDoesNotMatch):
The request signature we calculated does not
match the signature you provided.
nubecita dice por que: la firma no coincide
(revisa la peticion canonica: ruta, consulta
 o cabeceras)
```

## 4. los cuatro pasos, y son todos

```console
1. PETICION CANONICA   reescribir la peticion en un
                       formato exacto y sin ambiguedad
2. CADENA A FIRMAR     la fecha, el ambito, y el
                       resumen de lo anterior
3. CLAVE DE FIRMA      secreto -> fecha -> region ->
                       servicio -> aws4
4. FIRMA               HMAC de la cadena con esa clave
```

## 5. la cadena de la clave de firma

```console
secreto   +  20260903      ->  clave del dia
clave del dia  +  us-east-1  ->  clave de la region
clave de la region  +  s3    ->  clave del servicio
clave del servicio  +  aws4  ->  clave de FIRMA
```

## 6. lo que veras en el trafico

```console
x-amz-content-sha256: UNSIGNED-PAYLOAD
```

## 7. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
nubecita:curso -firmar
corrida: 2026-09-03 · salida-real.txt
```
