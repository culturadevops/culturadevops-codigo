# Salida ejecutada — vídeo 215 «Escribí S3 en Python»

> Corrida del 2026-09-07. Servidor: `s3_py.py` en `python:3.12-alpine`, solo biblioteca estándar.
> Cliente: **boto3 OFICIAL**, en otro contenedor, por red de Docker.
> Lo único que cambia respecto a producción es `endpoint_url`.

```
=== boto3 OFICIAL contra un S3 escrito en Python ===
  boto3 1.43.89

--- lo basico ---
  create_bucket  -> ok
  put_object     -> ETag "0ad066a5d29f3f2a2a1c7c17dd082a79"
  get_object     -> hola mundo
  head_object    -> ContentLength 10
  list_buckets   -> ['facturas']

--- el ETag es el MD5, y boto3 lo lee ---
  md5 local      = 0ad066a5d29f3f2a2a1c7c17dd082a79
  ETag del server= 0ad066a5d29f3f2a2a1c7c17dd082a79

--- LAS CARPETAS NO EXISTEN: son claves planas ---
  todas las claves, planas:
      2026/01/f1.pdf
      2026/01/f2.pdf
      2026/02/f3.pdf
      hola.txt
      raiz.txt

  y ahora el MISMO almacen, listado con delimiter='/':
     ficheros : ['hola.txt', 'raiz.txt']
     'carpetas': ['2026/']
     ^ eso lo calcula el LISTADO. No hay ninguna carpeta guardada.

  con Prefix='2026/' y delimiter='/':
     'carpetas': ['2026/01/', '2026/02/']

--- por eso RENOMBRAR UNA CARPETA no existe ---
  para renombrar 2026/01/ hay que copiar y borrar objeto a objeto:
     2026/01/f1.pdf  ->  2026/enero/f1.pdf
     2026/01/f2.pdf  ->  2026/enero/f2.pdf
     'carpetas' despues: ['2026/02/', '2026/enero/']
     ^ 4 llamadas por fichero. Con 10.000 ficheros, 40.000 llamadas.

--- lo que pasa cuando la clave no existe ---
  boto3 levanta su excepcion tipada: NoSuchKey
```

### 🥇 Lo que sostiene el vídeo 215

**Las carpetas no existen.** El almacén es un diccionario plano de claves. Lo que la consola de
AWS te pinta como un árbol lo calcula el LISTADO, en cada llamada, a partir de `prefix` y
`delimiter`. Se ve en la corrida: el mismo almacén listado sin delimitador da cinco claves
planas, y con `delimiter='/'` aparece una «carpeta» `2026/` que no está guardada en ningún sitio.

**Y por eso renombrar una carpeta no es una operación.** Hay que copiar y borrar objeto a objeto:
4 llamadas por fichero. Con 10.000 ficheros, 40.000 llamadas.

### 🐛 El fallo que boto3 destapó, y que se cuenta en el vídeo

Primera versión: `head_object` devolvía `ContentLength 0` para un objeto de 10 bytes.

Un `HEAD` no manda cuerpo, pero **tiene que declarar el tamaño del cuerpo que mandaría**. Yo puse
`Content-Length: 0` porque el cuerpo iba vacío, y el servidor respondía tan tranquilo. Nadie se
queja... salvo el cliente, que te cree. Es exactamente la clase de fallo que solo aparece cuando
enchufas el cliente de verdad en vez de tu propio script.

Corregido el 2026-09-07 con boto3 1.43.89.
