# Tu Lambda no recibe peticiones: las va a buscar (curso 6/8) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. lo unico que cambia

```console
docker run \
  -e AWS_LAMBDA_RUNTIME_API=nubecita:4566/f/saludar \
  funcion-saludar:1
```

## 2. 1 · el plano de datos · la llamas TU

```console
POST /2015-03-31/functions/saludar/invocations

{"nombre":"Ada"}
```

## 3. 2 · la API del runtime · la llama TU FUNCION

```console
GET  /2018-06-01/runtime/invocation/next
        <- y se queda AQUI esperando

POST /2018-06-01/runtime/invocation/{id}/response
```

## 4. primera invocacion · salida real

```console
$ aws ... lambda invoke --function-name saludar2 \
$        --payload ... salida.json
{"saludo":"hola, Ada",
 "frio":true,
 "invocacion":1,
 "contenedor":"7ff14abda72e"}
```

## 5. segunda invocacion · salida real

```console
$ aws ... lambda invoke --function-name saludar2 ...
{"saludo":"hola, Ada",
 "frio":false,
 "invocacion":2,
 "contenedor":"7ff14abda72e"}
```

## 6. la funcion falla · salida real

```console
$ aws ... lambda invoke --function-name saludar2 \
$        --payload ...fallar:true... salida.json
200   Unhandled
{"errorMessage":"me han pedido que falle,
  y he fallado","errorType":"errorString"}
```

## 7. el plazo viaja en una cabecera

```console
Lambda-Runtime-Deadline-Ms: 1788461247000

      -> y de ahi sale el ctx.Deadline()
         que le llega a tu manejador
```

## 8. el material del curso

```console
aws-lambda-go   ·  la biblioteca oficial
aws-cli/2.36.19 ·  la CLI oficial
corrida: 2026-09-03 · salida-real.txt
```
