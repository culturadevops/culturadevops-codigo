# -*- coding: utf-8 -*-
"""Lección 2 · El presupuesto, por código. Y lo que un presupuesto NO hace.

Un presupuesto mensual de 20 USD con dos avisos: el real al 80 % y el previsto al 100 %, creado
con la API (aquí contra moto). Y la trampa: AWS Budgets se actualiza hasta tres veces al día, y
avisa; no para nada. Lo que se puede gastar entre dos actualizaciones, calculado.
"""
import json
import sys
from pathlib import Path

import boto3
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import precios as PR  # noqa: E402

CUENTA = "123456789012"
with mock_aws():
    b = boto3.client("budgets", region_name="us-east-1")
    aviso = lambda tipo, pct: {"Notification": {"NotificationType": tipo, "ComparisonOperator": "GREATER_THAN",  # noqa: E731
                                                "Threshold": pct, "ThresholdType": "PERCENTAGE"},
                               "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "yo@ejemplo.dev"}]}
    b.create_budget(AccountId=CUENTA,
                    Budget={"BudgetName": "mi-cuenta", "BudgetLimit": {"Amount": "20", "Unit": "USD"},
                            "TimeUnit": "MONTHLY", "BudgetType": "COST"},
                    NotificationsWithSubscribers=[aviso("ACTUAL", 80), aviso("FORECASTED", 100)])
    print("\n== 2.1 · El presupuesto, creado con la API ==")
    p = b.describe_budget(AccountId=CUENTA, BudgetName="mi-cuenta")["Budget"]
    print(f"  {p['BudgetName']}: {p['BudgetLimit']['Amount']} {p['BudgetLimit']['Unit']} · {p['TimeUnit']} · {p['BudgetType']}")
    for n in b.describe_notifications_for_budget(AccountId=CUENTA, BudgetName="mi-cuenta")["Notifications"]:
        print(f"  aviso: {n['NotificationType']:10s} {n['ComparisonOperator']} {n['Threshold']:.0f} %")

print("\n== 2.2 · Lo que dice la documentación ==")
for l in (Path(__file__).resolve().parent.parent / "FUENTES.md").read_text(encoding="utf-8").splitlines():
    if l.startswith("- «") and ("updated up to" in l or "exceed your budget" in l):
        print("  " + l[2:])

print("\n== 2.3 · Lo que cabe entre dos actualizaciones (hasta 12 h) ==")
precio = PR.P["m7i_large_hora"][0]
for n in (1, 10):
    gasto = n * 12 * precio
    print(f"  {n:2d} × m7i.large lanzadas por error, 12 h: {PR.usd(gasto):>10s}  ({gasto / 20 * 100:.0f}% del presupuesto)")
print(f"\n  precios: {PR.fuentes()}")
