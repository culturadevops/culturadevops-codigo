# SALIDA — Curso de cloud desde cero · 3 · el presupuesto (demos ejecutadas)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-18 14:26 UTC
- aws-cli/2.36.5 Python/3.14.6 Windows/11 exe/AMD64
- moto 5.2.3 (emulador de la API de AWS)
- moto emula la API, no la factura ni todos los valores por defecto.

## Un presupuesto de 10 USD al mes, con dos avisos

`$ cat presupuesto.json`

```
{
  "BudgetName": "mi-cuenta-de-practica",
  "BudgetType": "COST",
  "TimeUnit": "MONTHLY",
  "BudgetLimit": {
    "Amount": "10",
    "Unit": "USD"
  }
}
```

`$ aws budgets create-budget --account-id 123456789012 --budget file://presupuesto.json --notifications-with-subscribers file://avisos.json`

```
(sin salida)
```

`$ aws budgets describe-notifications-for-budget --account-id 123456789012 --budget-name mi-cuenta-de-practica --query Notifications[].{Tipo:NotificationType,Umbral:Threshold}`

```
[
    {
        "Tipo": "ACTUAL",
        "Umbral": 50
    },
    {
        "Tipo": "FORECASTED",
        "Umbral": 100
    }
]
```

> moto guarda el presupuesto, pero no tiene facturación: no evalúa el gasto ni envía correos. En AWS, sí.
