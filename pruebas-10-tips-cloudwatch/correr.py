# -*- coding: utf-8 -*-
"""10 tips para CloudWatch — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

    python correr.py
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

Q_ALARMA = ("MetricAlarms[0].{Alarma:AlarmName,Periodo:Period,EvaluationPeriods:EvaluationPeriods,"
            "DatapointsToAlarm:DatapointsToAlarm,TreatMissingData:TreatMissingData,"
            "Acciones:AlarmActions}")

with Banco(AQUI, "10 tips para CloudWatch", puerto=5101) as b:
    b.titulo("Un grupo de logs recién creado")
    b.aws("logs", "create-log-group", "--log-group-name", "/app/pagos")
    b.aws("logs", "describe-log-groups", "--log-group-name-prefix", "/app/pagos",
          "--query", "logGroups[0].{Nombre:logGroupName,retentionInDays:retentionInDays}")
    b.aws("logs", "put-retention-policy", "--log-group-name", "/app/pagos",
          "--retention-in-days", "30")
    b.aws("logs", "describe-log-groups", "--log-group-name-prefix", "/app/pagos",
          "--query", "logGroups[0].{Nombre:logGroupName,retentionInDays:retentionInDays}")

    b.titulo("Una alarma creada solo con lo obligatorio")
    b.aws("cloudwatch", "put-metric-alarm", "--alarm-name", "cpu-alta", "--namespace", "AWS/EC2",
          "--metric-name", "CPUUtilization", "--statistic", "Average", "--period", "300",
          "--evaluation-periods", "3", "--threshold", "80",
          "--comparison-operator", "GreaterThanThreshold",
          "--dimensions", "Name=InstanceId,Value=i-0abc123",
          "--alarm-actions", "arn:aws:sns:us-east-1:123456789012:tema-que-no-existe")
    b.aws("cloudwatch", "describe-alarms", "--alarm-names", "cpu-alta", "--query",
          "MetricAlarms[0].{Alarma:AlarmName,Periodo:Period,Acciones:AlarmActions}")
    b.aws("sns", "list-topics", "--query", "length(Topics)")

    b.titulo("Tres de cinco, y datos que faltan")
    b.aws("cloudwatch", "put-metric-alarm", "--alarm-name", "errores-5xx", "--namespace", "MiApp",
          "--metric-name", "Errores5xx", "--statistic", "Sum", "--period", "60",
          "--evaluation-periods", "5", "--datapoints-to-alarm", "3", "--threshold", "10",
          "--comparison-operator", "GreaterThanThreshold", "--treat-missing-data", "notBreaching")
    b.aws("cloudwatch", "describe-alarms", "--alarm-names", "errores-5xx", "--query", Q_ALARMA)

    b.titulo("Cada combinación de dimensiones es otra métrica")
    for amb, reg in (("prod", "mx"), ("prod", "co"), ("staging", "mx")):
        b.aws("cloudwatch", "put-metric-data", "--namespace", "MiApp", "--metric-name", "Pedidos",
              "--value", "1", "--dimensions", f"Entorno={amb},Pais={reg}")
    b.aws("cloudwatch", "list-metrics", "--namespace", "MiApp", "--metric-name", "Pedidos",
          "--query", "Metrics[].Dimensions[].[Name,Value]", "--output", "text")
    b.aws("cloudwatch", "list-metrics", "--namespace", "MiApp", "--metric-name", "Pedidos",
          "--query", "length(Metrics)")

    # Alarma compuesta: moto 5.2.3 devuelve 500 en put-composite-alarm (con y sin comillas en la
    # regla). Fallo del emulador: ese tip va solo con la documentación.

    b.titulo("Probar una alarma sin esperar a que pase")
    b.aws("cloudwatch", "set-alarm-state", "--alarm-name", "cpu-alta", "--state-value", "ALARM",
          "--state-reason", "prueba manual")
    b.aws("cloudwatch", "describe-alarms", "--alarm-names", "cpu-alta",
          "--query", "MetricAlarms[0].{Alarma:AlarmName,Estado:StateValue,Motivo:StateReason}")
