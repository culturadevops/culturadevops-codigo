# -*- coding: utf-8 -*-
"""10 tips para AWS Budgets y Cost Explorer — demos con la AWS CLI contra moto. Escribe SALIDA.md.

⚠️ moto emula la API de Budgets, no tiene facturación real: los presupuestos no se evalúan ni
   envían avisos. Lo que se enseña es la configuración que acepta y devuelve la API.

    python correr.py
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

CUENTA = "123456789012"
PRESUPUESTO = {"BudgetName": "mensual-cuenta", "BudgetType": "COST", "TimeUnit": "MONTHLY",
               "BudgetLimit": {"Amount": "50", "Unit": "USD"}}
AVISOS = [
    {"Notification": {"NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN",
                      "Threshold": 80, "ThresholdType": "PERCENTAGE"},
     "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "equipo@example.com"}]},
    {"Notification": {"NotificationType": "FORECASTED", "ComparisonOperator": "GREATER_THAN",
                      "Threshold": 100, "ThresholdType": "PERCENTAGE"},
     "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "equipo@example.com"}]},
]

with Banco(AQUI, "10 tips para AWS Budgets y Cost Explorer", puerto=5105) as b:
    (AQUI / "presupuesto.json").write_text(json.dumps(PRESUPUESTO, indent=2), encoding="utf-8")
    (AQUI / "avisos.json").write_text(json.dumps(AVISOS, indent=2), encoding="utf-8")

    b.titulo("Un presupuesto mensual con dos avisos")
    b.anotar("cat presupuesto.json", (AQUI / "presupuesto.json").read_text(encoding="utf-8"))
    b.anotar("cat avisos.json   # resumido: tipo y umbral",
             "\n".join(f"{a['Notification']['NotificationType']:<11} > "
                       f"{a['Notification']['Threshold']} %  → {a['Subscribers'][0]['Address']}"
                       for a in AVISOS))
    b.aws("budgets", "create-budget", "--account-id", CUENTA, "--budget", "file://presupuesto.json",
          "--notifications-with-subscribers", "file://avisos.json")
    b.aws("budgets", "describe-budgets", "--account-id", CUENTA,
          "--query", "Budgets[].{Nombre:BudgetName,Tipo:BudgetType,Periodo:TimeUnit}")
    b.aws("budgets", "describe-notifications-for-budget", "--account-id", CUENTA,
          "--budget-name", "mensual-cuenta",
          "--query", "Notifications[].{Tipo:NotificationType,Umbral:Threshold}")
