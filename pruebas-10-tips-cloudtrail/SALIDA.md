# SALIDA — 10 tips para AWS CloudTrail (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 18:12 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## El bucket del trail y su política

`$ aws s3api put-bucket-policy --bucket auditoria-cuenta --policy file://politica.json`

```
(sin salida)
```

## Un trail creado con la CLI, solo con lo obligatorio

`$ aws cloudtrail create-trail --name auditoria --s3-bucket-name auditoria-cuenta`

```
{
    "Nombre": "auditoria",
    "MultiRegion": false,
    "Validacion": false
}
```

`$ aws cloudtrail get-trail-status --name auditoria --query IsLogging`

```
false
```

## Encenderlo

`$ aws cloudtrail start-logging --name auditoria`

```
(sin salida)
```

`$ aws cloudtrail get-trail-status --name auditoria --query IsLogging`

```
true
```

## Multirregión y validación de integridad

`$ aws cloudtrail update-trail --name auditoria --is-multi-region-trail --enable-log-file-validation`

```
{
    "MultiRegion": true,
    "Validacion": true
}
```

## Eventos de datos: no vienen por defecto

`$ aws cloudtrail get-event-selectors --trail-name auditoria`

```
[]
```

`$ aws cloudtrail put-event-selectors --trail-name auditoria --event-selectors file://selectores.json`

```
[
    {
        "Type": "AWS::S3::Object",
        "Values": [
            "arn:aws:s3:::datos-clientes/"
        ]
    }
]
```

## Cifrar los logs con tu clave de KMS

`$ aws cloudtrail update-trail --name auditoria --kms-key-id <arn de la clave>`

```
"arn:aws:kms:us-east-1:123456789012:key/eeed63b0-4710-446b-aa3e-d869497b8518"
```

## Enviar a CloudWatch Logs

`$ aws cloudtrail update-trail --name auditoria --cloud-watch-logs-log-group-arn <grupo> --cloud-watch-logs-role-arn <rol>`

```
"arn:aws:logs:us-east-1:123456789012:log-group:cloudtrail/auditoria:*"
```

`$ aws logs put-metric-filter --log-group-name cloudtrail/auditoria --filter-name uso-de-root ...`

```
(sin salida)
```

`$ aws logs describe-metric-filters --log-group-name cloudtrail/auditoria`

```
[
    {
        "Filtro": "uso-de-root",
        "Metrica": "UsoDeRoot"
    }
]
```

## El trail, al final

`$ aws cloudtrail describe-trails`

```
{
    "Nombre": "auditoria",
    "MultiRegion": true,
    "Validacion": true,
    "KMS": true,
    "Logs": true
}
```

## Apagarlo es una llamada

`$ aws cloudtrail stop-logging --name auditoria`

```
(sin salida)
```

`$ aws cloudtrail get-trail-status --name auditoria --query IsLogging`

```
false
```
