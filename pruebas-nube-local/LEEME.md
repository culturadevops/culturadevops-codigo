# Pruebas — Curso MIEMBROS «Tu nube local SIN licencias» (idea #77)

> **Todo se ejecutó el 2026-09-03.** `nubecita` (imagen local construida aquí, **10,5 MB**) contra
> la **CLI oficial de AWS** (`amazon/aws-cli`, **aws-cli/2.36.19**), las dos en la misma red de
> Docker. Salida literal y sin retocar en [`salida-real.txt`](salida-real.txt).

## El argumento del curso, y por qué la evidencia es así

Quien habla con el doble es **siempre el cliente oficial de Amazon**. No hay parche, no hay
biblioteca de pruebas, no hay «modo local». Lo único que cambia en toda la corrida es
`--endpoint-url`. Si el cliente oficial no nota la diferencia, el doble sirve.

Por eso ni una sola orden de la evidencia es de nubecita: son `aws s3`, `aws dynamodb`,
`aws sqs`, `aws sns` y `aws lambda`, tal cual.

## Cómo se reproduce

```sh
docker network create curso-nube
docker build -t nubecita:curso <nubecita>
docker build -t funcion-saludar:1 <nubecita>/ejemplo-funcion

docker run -d --name nubecita --network curso-nube nubecita:curso -escuchar 0.0.0.0
MSYS_NO_PATHCONV=1 docker run --rm --network curso-nube -v "$(pwd -W):/lab" \
    --entrypoint sh amazon/aws-cli:latest /lab/correr.sh
```

⚠️ **`MSYS_NO_PATHCONV=1` no es opcional en Windows.** Sin ella, Git Bash reescribe
`-docker /var/run/docker.sock` a `C:/Program Files/Git/var/run/docker.sock` **dentro del
argumento**, y el lanzador falla con un `no such file or directory` que señala una ruta que
nadie escribió. Pasó en esta misma corrida y cuesta un rato entenderlo. Va en el episodio 7.

---

## EP1 · El primer bucket, con la CLI oficial

```
aws-cli/2.36.19 Python/3.14.6 Linux/6.18.33.2-microsoft-standard-WSL2
make_bucket: fotos
2026-09-03 18:53:27 fotos
```

## EP2 · S3 no tiene carpetas 🥇

Es la lección que no se olvida, y se ve con tres órdenes:

```
-- ls plano: 2026/ aparece como PRE(fijo), que no es una carpeta --
                           PRE 2026/
2026-09-03 18:53:28          8 gato.txt
-- ls --recursive: la 'carpeta' era parte del NOMBRE --
2026-09-03 18:53:28          6 2026/enero/nota.txt
-- sin delimitador: la clave entera es el nombre --
["2026/enero/nota.txt", "gato.txt"]
```

👉 **Quien inventa las carpetas es el delimitador `/`, no S3.** La clave es una cadena plana.

## EP3 · DynamoDB: otro protocolo, el mismo puerto

S3 dice qué quiere con el **método y la ruta**. DynamoDB manda **siempre** `POST /` con la
operación en la cabecera `X-Amz-Target`. Dos servicios de la misma nube, dos diseños — S3 es de
2006 y DynamoDB de 2012. Y los dos entran por el mismo puerto porque el enrutador mira la cabecera.

```
pedidos
-- Query: SOLO la particion de ana, y ya viene ordenado --
["2026-01-03", "2026-02-11"]
-- Scan: recorre la tabla ENTERA. Por eso se paga --
3
```

## EP4 · SQS: recibir no saca el mensaje, lo esconde 🥇

```
-- 1a recepcion --                    [["procesa el pedido 42", "1"]]
-- 2a recepcion INMEDIATA --          null
ApproximateNumberOfMessages:            0
ApproximateNumberOfMessagesNotVisible:  1
```

👉 El mensaje **no se perdió**: está invisible durante su `VisibilityTimeout` (30 s). Ese cero
con un uno al lado es toda la entrega «al menos una vez» en dos números.

### EP4b · SNS: tu mensaje no viaja solo

```
{"Type":"Notification","MessageId":"avisos-2","TopicArn":"...:avisos",
 "Message":"se cayo el disco","Timestamp":"2026-09-03T18:53:34.973Z"}
```

👉 Publicas `se cayo el disco` y en la cola aparece **un sobre** con tu mensaje dentro. El
consumidor que espere tu texto en crudo va a leer JSON.

## EP5 · La firma: `-firmar` 🥇

```
-- la credencial BUENA entra --
make_bucket: privado2
-- la credencial MALA --
An error occurred (SignatureDoesNotMatch) ... The request signature we calculated does not
match the signature you provided. nubecita dice por qué: la firma no coincide
(revisa la petición canónica: ruta, consulta o cabeceras)
```

👉 **Lo que hace único al laboratorio:** AWS de verdad te da `SignatureDoesNotMatch` y punto —
nunca el motivo, a propósito. Aquí el doble **sí lo dice**. Se aprende depurando lo que en
producción es una pared.

## EP6-7 · Lambda, y que los contenedores los levante ella 🥇

La función está compilada con **`aws-lambda-go`, la biblioteca oficial de Amazon**, sin una
línea distinta. Lo único que cambia es `AWS_LAMBDA_RUNTIME_API`.

```
saludar2   Image   Active          <- crear NO levanta nada
-- 1a invocacion: FRIO --
{"saludo":"hola, Ada","frio":true,"invocacion":1,"contenedor":"7ff14abda72e"}
-- 2a invocacion: MISMO contenedor. TEMPLADO --
{"saludo":"hola, Ada","frio":false,"invocacion":2,"contenedor":"7ff14abda72e"}
-- la funcion FALLA. El codigo HTTP es 200 --
200   Unhandled
{"errorMessage":"me han pedido que falle, y he fallado","errorType":"errorString"}
```

Medido aparte, con `time`: **frío 0,487 s · templado 0,312 s**. Y el apagado por ocioso, en el
registro del propio servicio:

```
-> apagado 83496c8452f6: saludar llevaba 35s sin invocarse
```

👉 **Tres hallazgos que valen los dos episodios:**
1. `crear` no ejecuta nada. El contenedor aparece en la **primera invocación**, y esa espera
   *es* el arranque en frío.
2. La segunda invocación cae en el **mismo contenedor** (`invocacion: 2`): por eso las variables
   de paquete sobreviven, y por eso guardar estado en una global es una trampa.
3. 🥇 **Una función que falla contesta `200`.** El fallo viaja en `X-Amz-Function-Error`. Un
   cliente que solo mire el código HTTP trata como éxito **cada fallo de tu función**.

## EP8 · La semilla: pruebas que arrancan siempre del mismo sitio

```
sha256 de la semilla ANTES:   de5bca04112fca24
-- lo que trae puesto, sin que nadie lo suba --
2026-09-03 18:49:11         22 contrato.txt
-- escribo algo nuevo: entra, pero solo en memoria --
                            22 contrato.txt
                             5 h.txt
sha256 de la semilla DESPUES: de5bca04112fca24
```

👉 Con `-semilla` lee al arrancar y **no escribe nunca**. Es lo que hace repetible una suite en
integración continua: cada corrida parte del mismo estado, sin limpieza previa y sin residuos.

⚠️ Y el fichero de estado **hay que generarlo, no escribirlo a mano**: nubecita valida con
`DisallowUnknownFields` y rechaza un JSON con la forma equivocada. Se genera arrancando con
`-datos` y dejando que lo escriba ella. (Se intentó a mano en esta corrida y lo rechazó, que es
justo lo que tiene que hacer.)

---

## Lo que este material NO demuestra

- **nubecita no es producción y no lo va a ser.** Es un doble de pruebas, y vale por lo que
  **no** hace: no hay disco de verdad, ni políticas, ni durabilidad.
- **No cubre AWS entero.** No hay índices secundarios, `UpdateItem`, transacciones, streams,
  colas FIFO, firmas en la URL, STS ni permisos por política. La frontera está en el README.
- **No se midió rendimiento contra LocalStack ni contra AWS.** Los dos únicos tiempos que se
  citan (0,487 s en frío y 0,312 s templado) son de arranque de contenedor en esta máquina, y se
  presentan como tales.
- El tamaño de imagen **10,5 MB es lo que ocupa en disco**, no lo que se descarga. Son dos
  números distintos y confundirlos publica una cifra falsa.
