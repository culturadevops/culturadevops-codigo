# SALIDA — 10 tips para CloudWatch (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 00:12 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Un grupo de logs recién creado

`$ aws logs create-log-group --log-group-name /app/pagos`

```
(sin salida)
```

`$ aws logs describe-log-groups --log-group-name-prefix /app/pagos --query logGroups[0].{Nombre:logGroupName,retentionInDays:retentionInDays}`

```
{
    "Nombre": "/app/pagos",
    "retentionInDays": null
}
```

`$ aws logs put-retention-policy --log-group-name /app/pagos --retention-in-days 30`

```
(sin salida)
```

`$ aws logs describe-log-groups --log-group-name-prefix /app/pagos --query logGroups[0].{Nombre:logGroupName,retentionInDays:retentionInDays}`

```
{
    "Nombre": "/app/pagos",
    "retentionInDays": 30
}
```

## Una alarma creada solo con lo obligatorio

`$ aws cloudwatch put-metric-alarm --alarm-name cpu-alta --namespace AWS/EC2 --metric-name CPUUtilization --statistic Average --period 300 --evaluation-periods 3 --threshold 80 --comparison-operator GreaterThanThreshold --dimensions Name=InstanceId,Value=i-0abc123 --alarm-actions arn:aws:sns:us-east-1:123456789012:tema-que-no-existe`

```
(sin salida)
```

`$ aws cloudwatch describe-alarms --alarm-names cpu-alta --query MetricAlarms[0].{Alarma:AlarmName,Periodo:Period,Acciones:AlarmActions}`

```
{
    "Alarma": "cpu-alta",
    "Periodo": 300,
    "Acciones": [
        "arn:aws:sns:us-east-1:123456789012:tema-que-no-existe"
    ]
}
```

`$ aws sns list-topics --query length(Topics)`

```
0
```

## Tres de cinco, y datos que faltan

`$ aws cloudwatch put-metric-alarm --alarm-name errores-5xx --namespace MiApp --metric-name Errores5xx --statistic Sum --period 60 --evaluation-periods 5 --datapoints-to-alarm 3 --threshold 10 --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching`

```
(sin salida)
```

`$ aws cloudwatch describe-alarms --alarm-names errores-5xx --query MetricAlarms[0].{Alarma:AlarmName,Periodo:Period,EvaluationPeriods:EvaluationPeriods,DatapointsToAlarm:DatapointsToAlarm,TreatMissingData:TreatMissingData,Acciones:AlarmActions}`

```
{
    "Alarma": "errores-5xx",
    "Periodo": 60,
    "EvaluationPeriods": 5,
    "DatapointsToAlarm": 3,
    "TreatMissingData": "notBreaching",
    "Acciones": []
}
```

## Cada combinación de dimensiones es otra métrica

`$ aws cloudwatch put-metric-data --namespace MiApp --metric-name Pedidos --value 1 --dimensions Entorno=prod,Pais=mx`

```
(sin salida)
```

`$ aws cloudwatch put-metric-data --namespace MiApp --metric-name Pedidos --value 1 --dimensions Entorno=prod,Pais=co`

```
(sin salida)
```

`$ aws cloudwatch put-metric-data --namespace MiApp --metric-name Pedidos --value 1 --dimensions Entorno=staging,Pais=mx`

```
(sin salida)
```

`$ aws cloudwatch list-metrics --namespace MiApp --metric-name Pedidos --query Metrics[].Dimensions[].[Name,Value] --output text`

```
Entorno	prod
Pais	mx
Entorno	prod
Pais	co
Entorno	staging
Pais	mx
```

`$ aws cloudwatch list-metrics --namespace MiApp --metric-name Pedidos --query length(Metrics)`

```
3
```

## Probar una alarma sin esperar a que pase

`$ aws cloudwatch set-alarm-state --alarm-name cpu-alta --state-value ALARM --state-reason prueba manual`

```
(sin salida)
```

`$ aws cloudwatch describe-alarms --alarm-names cpu-alta --query MetricAlarms[0].{Alarma:AlarmName,Estado:StateValue,Motivo:StateReason}`

```
{
    "Alarma": "cpu-alta",
    "Estado": "ALARM",
    "Motivo": "prueba manual"
}
```
