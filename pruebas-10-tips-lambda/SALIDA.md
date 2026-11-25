# SALIDA — 10 tips para Lambda (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:50 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura: los costos los dice la documentación.

## Los valores por defecto de una función

`$ aws lambda create-function --function-name procesar --runtime python3.13 --handler app.handler --role <rol> --zip-file fileb://funcion.zip`

```
{
    "Timeout": 3,
    "MemorySize": 128,
    "Architectures": [
        "x86_64"
    ]
}
```

`$ aws lambda update-function-configuration --function-name procesar --timeout 30 --memory-size 1769 --query {Timeout:Timeout,MemorySize:MemorySize}`

```
{
    "Timeout": 30,
    "MemorySize": 1769
}
```

## Logs que no caducan nunca

`$ aws logs create-log-group --log-group-name /aws/lambda/procesar`

```
(sin salida)
```

`$ aws logs describe-log-groups --log-group-name-prefix /aws/lambda/procesar --query logGroups[].{Grupo:logGroupName,DiasDeRetencion:retentionInDays}`

```
[
    {
        "Grupo": "/aws/lambda/procesar",
        "DiasDeRetencion": null
    }
]
```

`$ aws logs put-retention-policy --log-group-name /aws/lambda/procesar --retention-in-days 14`

```
(sin salida)
```

`$ aws logs describe-log-groups --log-group-name-prefix /aws/lambda/procesar --query logGroups[].{Grupo:logGroupName,DiasDeRetencion:retentionInDays}`

```
[
    {
        "Grupo": "/aws/lambda/procesar",
        "DiasDeRetencion": 14
    }
]
```

## Una Function URL sin autenticación

`$ aws lambda create-function-url-config --function-name procesar --auth-type NONE --query {Url:FunctionUrl,Auth:AuthType}`

```
{
    "Url": "https://51222aec58174787bafcaf0e0e8043b1.lambda-url.us-east-1.on.aws",
    "Auth": "NONE"
}
```

## Concurrencia reservada: tope y freno

`$ aws lambda put-function-concurrency --function-name procesar --reserved-concurrent-executions 10`

```
{
    "ReservedConcurrentExecutions": 10
}
```

`$ aws lambda put-function-concurrency --function-name procesar --reserved-concurrent-executions 0`

```
{
    "ReservedConcurrentExecutions": 0
}
```

`$ aws lambda get-function-concurrency --function-name procesar`

```
{
    "ReservedConcurrentExecutions": 0
}
```
