# Tu laboratorio de AWS dejó de ser gratis: monta el recambio en un minuto — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo que cambio

```console
23-mar-2026 · se acabo la edicion Community

  · una sola imagen
  · pide cuenta y token
  · el plan gratuito EXCLUYE el uso comercial
```

## 2. arrancar el laboratorio

```console
$ docker build -t nubecita:curso .
$ docker run -d --name nubecita -p 4566:4566 \
$        nubecita:curso -escuchar 0.0.0.0
```

## 3. lo que dice al arrancar · salida real

```console
nubecita · S3, DynamoDB, SQS, SNS, Logs y Lambda
en http://0.0.0.0:4566
  · sin comprobar firmas          -> episodio 5
  · sin permisos                  -> episodio 5
  · sin guardar nada              -> episodio 8
  · sin levantar runtimes         -> episodio 7
```

## 4. el primer bucket · salida real

```console
$ export AWS_ACCESS_KEY_ID=prueba
$ export AWS_SECRET_ACCESS_KEY=prueba
$ aws --endpoint-url http://localhost:4566 s3 mb s3://fotos
make_bucket: fotos
```

## 5. quien esta hablando de verdad

```console
$ aws --version
aws-cli/2.36.19 Python/3.14.6 Linux/6.18.33.2
```

## 6. las dos lineas, en Go

```console
c := s3.New(s3.Options{
    Region:       "us-east-1",
    BaseEndpoint: aws.String("http://127.0.0.1:4566"),
    UsePathStyle: true,
})
```

## 7. como se cablea sin ensuciar el codigo

```console
punto := os.Getenv("AWS_ENDPOINT_URL")

if punto != "" {
        opciones.BaseEndpoint = aws.String(punto)
        opciones.UsePathStyle = true
}
```

## 8. el material del curso

```console
nubecita:curso   ·  10,5 MB en disco
aws-cli/2.36.19  ·  la oficial de Amazon
corrida: 2026-09-03 · salida-real.txt
```
