# SALIDA — 10 tips para AWS Budgets y Cost Explorer (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-10 00:21 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Un presupuesto mensual con dos avisos

`$ cat presupuesto.json`

```
{
  "BudgetName": "mensual-cuenta",
  "BudgetType": "COST",
  "TimeUnit": "MONTHLY",
  "BudgetLimit": {
    "Amount": "50",
    "Unit": "USD"
  }
}
```

`$ cat avisos.json   # resumido: tipo y umbral`

```
ACTUAL      > 80 %  → equipo@example.com
FORECASTED  > 100 %  → equipo@example.com
```

`$ aws budgets create-budget --account-id 123456789012 --budget file://presupuesto.json --notifications-with-subscribers file://avisos.json`

```
(sin salida)
```

`$ aws budgets describe-budgets --account-id 123456789012 --query Budgets[].{Nombre:BudgetName,Tipo:BudgetType,Periodo:TimeUnit}`

```
[
    {
        "Nombre": "mensual-cuenta",
        "Tipo": "COST",
        "Periodo": "MONTHLY"
    }
]
```

`$ aws budgets describe-notifications-for-budget --account-id 123456789012 --budget-name mensual-cuenta --query Notifications[].{Tipo:NotificationType,Umbral:Threshold}`

```
[
    {
        "Tipo": "ACTUAL",
        "Umbral": 80
    },
    {
        "Tipo": "FORECASTED",
        "Umbral": 100
    }
]
```
