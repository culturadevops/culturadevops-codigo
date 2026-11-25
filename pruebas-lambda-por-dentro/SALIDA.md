# Lambda por dentro — evidencia ejecutada (2026-09-20)

Entorno: `nubecita` (Go) en Docker 29.6.2 · CLI oficial `aws-cli/2.36.5` · `boto3 1.43.57`
Arranque: `docker run -d --rm -p 4566:4566 --network demo --name nubecita -v /var/run/docker.sock:/var/run/docker.sock nubecita -escuchar 0.0.0.0 -docker /var/run/docker.sock -red demo -yo nubecita:4566 -max 3 -ocioso 45s`

## 1. Crear una funcion NO levanta nada
    aws lambda create-function --function-name saludar --package-type Image --code ImageUri=funcion-saludar:1
    estado: Active · PackageType: Image
    docker ps --filter network=demo  ->  NINGUN contenedor de runtime
En esto no se paga por tener: se paga por ejecutar.

## 2. Frio contra caliente — EL MISMO contenedor
    1a invocacion   665 ms   {"frio":true,  "invocacion":1, "contenedor":"be907fb19173"}
    2a invocacion   454 ms   {"frio":false, "invocacion":2, "contenedor":"be907fb19173"}
El contador `invocacion` sube: el estado global del proceso sigue ahi entre invocaciones.

## 3. Apagado por ocioso (scale to zero)
    (52 s sin invocar)
    docker ps  ->  ninguno
    log literal: "-> apagado be907fb19173: saludar llevaba 47s sin invocarse"

## 4. Tu funcion falla y contesta 200  (desde boto3)
    invoke(Payload={"fallar": true})
      StatusCode ....... 200        <-- doscientos
      FunctionError .... Unhandled
      cuerpo ........... {"errorMessage":"me han pedido que falle, y he fallado","errorType":"errorString"}
    invoke(Payload={"nombre":"Ada"})
      StatusCode 200 · FunctionError None
Las dos son 200. Quien vigile el codigo HTTP no ve ni un fallo.

## 5. El tope de concurrencia no da error: da lentitud
Tope 3 runtimes · 6 invocaciones simultaneas de 2000 ms:
    inv 1   2010 ms   HTTP 200   01cf0932b60f
    inv 2   2138 ms   HTTP 200   9b4811aacbe2
    inv 0   2278 ms   HTTP 200   943229c39b6d
    inv 3   4013 ms   HTTP 200   01cf0932b60f
    inv 5   4128 ms   HTTP 200   9b4811aacbe2
    inv 4   4275 ms   HTTP 200   943229c39b6d
    contenedores distintos: 3 · ninguna dio error: True
Las tres ultimas tardan el DOBLE porque esperan turno ANTES de empezar.

## 6. Gotcha reproducido en vivo (Windows + Git Bash)
Sin `MSYS_NO_PATHCONV=1`, la consola reescribe `-v /var/run/docker.sock:/var/run/docker.sock`
y el contenedor no arranca. Es el mismo tropiezo que ya cuenta el video 186 del canal.
