#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a_mano.py — desplegar infraestructura con un guion de Python y el kit de AWS.
Vídeo 228.

⛔ ESTO NO ES UN HOMBRE DE PAJA: es exactamente por donde empieza todo el mundo, y funciona.
Un cubo de almacenamiento, una cola y una función. Tres llamadas y a correr.

La pregunta del vídeo no es si esto funciona (funciona), sino qué le falta. Y lo que le falta
se ve ejecutándolo DOS veces.
"""
import boto3

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# 1 · el cubo
s3.create_bucket(Bucket="mi-app-fotos")

# 2 · la cola
sqs.create_queue(QueueName="mi-app-trabajos")

# 3 · y activar el versionado del cubo, que es un segundo paso aparte
s3.put_bucket_versioning(
    Bucket="mi-app-fotos",
    VersioningConfiguration={"Status": "Enabled"},
)

print("listo")
