# S3 desde Python: el fallo silencioso que te deja fuera 500 objetos — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. subir un archivo del disco

```console
from lab import s3

s3.upload_file("foto.jpg",
               "fotos",
               "album/foto.jpg")

subido
```

## 2. subir contenido que ya tienes en memoria

```console
s3.put_object(Bucket="fotos",
              Key="nota.txt",
              Body=b"hola")

# y para leerlo de vuelta:
s3.get_object(Bucket="fotos",
              Key="nota.txt")["Body"].read()

b'hola'
```

## 3. bajarlo de vuelta

```console
s3.download_file("fotos",
                 "album/foto.jpg",
                 "bajada.jpg")

descargado, bytes: 1000
```

## 4. listar lo que hay dentro

```console
r = s3.list_objects_v2(Bucket="fotos")
claves = [o["Key"]
          for o in r.get("Contents", [])]
print(claves)

['album/foto.jpg']
```

## 5. 1.500 subidos, ¿cuántos devuelve?

```console
$ python pagina.py

  subiendo... 0
  subiendo... 500
  subiendo... 1000

list_objects_v2 devuelve: 1000
IsTruncated: True
```

## 6. la forma que no se deja nada

```console
p = s3.get_paginator("list_objects_v2")

n = 0
for pagina in p.paginate(Bucket="fotos",
                         Prefix="masivo/"):
    n += len(pagina.get("Contents", []))

con paginador: 1500
```

## 7. borrar aprovechando las páginas

```console
p = s3.get_paginator("list_objects_v2")

for pagina in p.paginate(Bucket="fotos"):
    objetos = [{"Key": o["Key"]}
               for o in pagina.get("Contents", [])]
    if objetos:
        s3.delete_objects(Bucket="fotos",
            Delete={"Objects": objetos})
```

## 8. generar una dirección temporal

```console
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": "fotos",
            "Key": "album/foto.jpg"},
    ExpiresIn=3600)

# una hora de validez
```

## 9. preparar el escenario de una prueba

```console
def preparar(n):
    s3.create_bucket(Bucket="pruebas")
    for i in range(n):
        s3.put_object(
            Bucket="pruebas",
            Key="f/%04d.txt" % i,
            Body=b"x")
```
