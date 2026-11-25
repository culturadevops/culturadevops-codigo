#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""app.py — LA MISMA infraestructura del guion a mano, pero con CDK.
Vídeo 228. Un cubo con versionado, una cola, y nada más.

⛔ La comparacion vale porque las dos versiones crean lo MISMO. Ni una pieza mas ni una menos.
"""
import aws_cdk as cdk
from aws_cdk import aws_s3 as s3, aws_sqs as sqs
from constructs import Construct


class MiApp(cdk.Stack):
    def __init__(self, ambito: Construct, iden: str, **kw):
        super().__init__(ambito, iden, **kw)

        # El versionado NO es un segundo paso: es un argumento. Esa es la diferencia
        # entre describir y dar ordenes.
        s3.Bucket(self, "Fotos",
                  bucket_name="mi-app-fotos",
                  versioned=True)

        sqs.Queue(self, "Trabajos",
                  queue_name="mi-app-trabajos")


app = cdk.App()
MiApp(app, "MiApp")
app.synth()
