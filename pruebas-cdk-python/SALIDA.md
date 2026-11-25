# Salida ejecutada — vídeo 228 «De un script de Python a CDK»

> Corrida del 2026-09-09. `cdk synth` con AWS CDK **2.1141.0** en `node:22-alpine`, sin
> credenciales y sin desplegar nada. La prueba de idempotencia, contra `nubecita` (la nube de
> mentira de la casa) en su propia red de Docker.

---

## Las dos versiones crean LO MISMO

Un cubo de almacenamiento con versionado y una cola. Ni una pieza más ni una menos, o la
comparación no vale nada.

```
   a_mano.py   (boto3)        15 líneas de código
   cdk/app.py  (AWS CDK)      16 líneas de código
```

**Empatan.** Así que el argumento no puede ser «con CDK escribes menos», porque es falso a esta
escala. Lo que cambia es otra cosa.

## 🥇 1 · LO QUE PASA AL EJECUTARLO DOS VECES

```
=== 1a ejecucion ===
listo

=== 2a ejecucion, la misma ===
botocore.errorfactory.BucketAlreadyOwnedByYou: An error occurred
(BucketAlreadyOwnedByYou) when calling the CreateBucket operation:
Your previous request to create the named bucket succeeded and you already own it.
```

El guion no sabe que ya existe. No es idempotente, y no puede serlo: **da órdenes**, no describe un
destino. Cada vez que quieras añadir algo tendrás que escribir un «si no existe» a mano, y
mantenerlo, para cada recurso, para siempre.

> ⚠️ **Nota honesta sobre esta prueba.** Se ejecuta `a_mano_min.py`, que es el mismo guion sin el
> paso del versionado. El motivo es una limitación de MI emulador: `nubecita` no implementa
> `PutBucketVersioning` y devolvía un error que tapaba el que este vídeo quiere enseñar. Lo
> comprobé por separado (`versionado NO implementado por nubecita`). Contra AWS de verdad, el
> guion completo se comporta igual: la segunda pasada falla al crear el cubo.

## 🥇 2 · 16 LÍNEAS DE PYTHON → 338 LÍNEAS DE PLANTILLA

```
$ cdk synth
338  cdk.out/MiApp.template.json
```

Y el desglose es lo interesante de verdad:

| sección de la plantilla | líneas |
|---|---|
| **Resources** (lo que de verdad pediste) | **37** |
| Conditions | **266** |
| Rules | 27 |
| Parameters | 7 |
| **total** | **338** |

**266 de las 338 líneas son UNA sola condición.** Y es esta:

```json
"CDKMetadataAvailable": { "Fn::Or": [ ... "af-south-1" ... "ap-east-1" ... ] }
```

Una lista gigante de todas las regiones de AWS, generada para decidir si CDK puede enviar su
bloque de telemetría. El 79 % de lo que genera tu herramienta no es tu infraestructura: es la
herramienta comprobando si puede llamar a casa.

## 🥇 3 · LA DECISIÓN QUE TOMÓ POR TI Y NO ESCRIBISTE

Esto es lo que más me sorprendió al leer la plantilla:

```
  FotosB2FC470F      AWS::S3::Bucket      DeletionPolicy = Retain
  Trabajos217F26D9   AWS::SQS::Queue      DeletionPolicy = Delete
```

**Dos recursos, dos políticas distintas, y ninguna de las dos la escribí yo.** CDK decidió que un
cubo de almacenamiento se conserva al destruir la pila y que una cola se borra.

Es una decisión sensata —los datos no se tiran— pero es una decisión, y tiene consecuencias que
nadie te cuenta: destruyes la pila, crees que has borrado todo, y el cubo sigue ahí facturando. Y
la próxima vez que despliegues con el mismo nombre, fallará porque ya existe y **ya no es tuyo**
desde el punto de vista de la pila.

## 4 · Y el bloque que va a la casa madre

```json
"CDKMetadata": {
  "Type": "AWS::CDK::Metadata",
  "Properties": { "Analytics": "v2:deflate64:H4sIAAAAAAAA/zPSMzKz0DNQTCwv1k1O..." }
}
```

Eso es una cadena comprimida con qué componentes de CDK has usado. Es la razón de ser de las 266
líneas de condiciones. Se puede desactivar, y el vídeo dice cómo.

---

## El resumen que ordena el vídeo

| | guion a mano | CDK |
|---|---|---|
| líneas que escribes | 15 | 16 |
| ejecutarlo dos veces | **revienta** | sin cambios |
| ¿sabe qué creó? | no | sí (la pila) |
| lo que genera | nada | 338 líneas, 37 tuyas |
| decisiones que toma por ti | ninguna | **política de borrado por recurso** |

**No se gana en líneas: se gana en que alguien lleva la cuenta.** Y se paga con una capa que toma
decisiones que no escribiste.

## ⛔ Lo que NO se hace aquí, y por qué

No hay despliegue real contra AWS. Las credenciales de esta máquina no funcionan
(`SignatureDoesNotMatch` con los dos perfiles, comprobado antes). `cdk synth` no las necesita, y
es donde está todo lo interesante de este vídeo: lo que se genera. El `cdk deploy` queda para
quien tenga cuenta.
