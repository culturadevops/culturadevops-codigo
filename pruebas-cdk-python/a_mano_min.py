#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a_mano_min.py — el MISMO guion que a_mano.py pero sin el paso del versionado.
⚠️ Existe SOLO por una limitacion de la nube de mentira contra la que se prueba: `nubecita` no
implementa PutBucketVersioning, y ese fallo suyo tapaba el fallo que este vídeo quiere enseñar.
La prueba de idempotencia sale igual: lo que se demuestra es que crear dos veces revienta.
"""
import boto3
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
s3.create_bucket(Bucket="mi-app-fotos")
sqs.create_queue(QueueName="mi-app-trabajos")
print("listo")
