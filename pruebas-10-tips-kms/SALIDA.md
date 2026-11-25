# SALIDA — 10 tips para AWS KMS (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 00:16 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Una clave creada solo con lo obligatorio

`$ aws kms create-key --description datos-de-pagos --query KeyMetadata.KeyId --output text`

```
fc95e2f5-7496-42e5-bcb1-afae16d748e8
```

`$ aws kms get-key-policy --key-id <clave> --policy-name default`

```
{"Version": "2012-10-17", "Id": "key-default-1", "Statement": [{"Sid": "Enable IAM User Permissions", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"}, "Action": "kms:*", "Resource": "*"}]}
```

`$ aws kms get-key-rotation-status --key-id <clave>`

```
{
    "KeyRotationEnabled": false
}
```

## Rotación automática

`$ aws kms enable-key-rotation --key-id <clave> --rotation-period-in-days 30`

```
aws: [ERROR]: An error occurred (ParamValidation): Parameter validation failed:
Invalid value for parameter RotationPeriodInDays, value: 30, valid min value: 90
```

`$ aws kms enable-key-rotation --key-id <clave> --rotation-period-in-days 180`

```
(sin salida)
```

`$ aws kms get-key-rotation-status --key-id <clave>`

```
{
    "KeyRotationEnabled": true
}
```

## Un alias, y cifrar con él

`$ aws kms create-alias --alias-name alias/pagos --target-key-id <clave>`

```
(sin salida)
```

`$ aws kms encrypt --key-id alias/pagos --plaintext fileb://secreto.txt --query CiphertextBlob --output text`

```
ZmM5NWUyZjUtNzQ5Ni00MmU1LWJjYjEtYWZhZTE2ZDc0OGU4TqaubT8QhRRC7HRxajL6SiFMvRuuY/06eot4Mcz3z/tyL2XchJNsjSxo2feFIw37iBFVSh1G2w==
```

## Rotar no cambia la clave ni rompe lo cifrado

`$ aws kms rotate-key-on-demand --key-id <clave>`

```
{
    "KeyId": "fc95e2f5-7496-42e5-bcb1-afae16d748e8"
}
```

`$ aws kms describe-key --key-id alias/pagos  # ¿el mismo id?`

```
fc95e2f5-7496-42e5-bcb1-afae16d748e8
```

`$ aws kms decrypt --ciphertext-blob fileb://cifrado.bin  # cifrado ANTES de rotar`

```
numero-de-tarjeta-de-prueba
```

## Programar el borrado

`$ aws kms schedule-key-deletion --key-id <clave> --pending-window-in-days 7 && aws kms describe-key ...KeyState`

```
"PendingDeletion"
```

`$ aws kms cancel-key-deletion --key-id <clave> && aws kms describe-key ...KeyState`

```
"Disabled"
```
