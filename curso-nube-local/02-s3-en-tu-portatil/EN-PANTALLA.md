# S3 en tu portátil: renombrar una carpeta no existe, y ahora vas a ver por qué — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. subir dos ficheros · salida real

```console
$ aws --endpoint-url http://localhost:4566 s3 mb s3://fotos
make_bucket: fotos
$ aws ... s3 cp gato.txt s3://fotos/gato.txt
$ aws ... s3 cp nota.txt s3://fotos/2026/enero/nota.txt
```

## 2. 1 · ls plano · salida real

```console
$ aws ... s3 ls s3://fotos/
                           PRE 2026/
2026-09-03 18:53:28          8 gato.txt
```

## 3. 2 · ls --recursive · salida real

```console
$ aws ... s3 ls s3://fotos/ --recursive
2026-09-03 18:53:28      6 2026/enero/nota.txt
2026-09-03 18:53:28      8 gato.txt
```

## 4. 3 · la API cruda · salida real

```console
$ aws ... s3api list-objects-v2 --bucket fotos \
$        --query 'Contents[].Key'
[
    "2026/enero/nota.txt",
    "gato.txt"
]
```

## 5. quien INVENTA las carpetas · salida real

```console
$ aws ... s3api list-objects-v2 --bucket fotos \
$        --delimiter / --query 'CommonPrefixes[].Prefix'
[
    "2026/"
]
```

## 6. lo que ya puedes hacer, igual que contra Amazon

```console
aws ... s3 sync ./local s3://fotos/copia/
aws ... s3 ls s3://fotos/ --recursive
aws ... s3 rm s3://fotos/2026/ --recursive
aws ... s3 rb s3://fotos --force
```

## 7. el material del curso

```console
aws-cli/2.36.19  ·  la oficial de Amazon
nubecita:curso   ·  10,5 MB en disco
corrida: 2026-09-03 · salida-real.txt
```
