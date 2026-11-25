# -*- coding: utf-8 -*-
"""Flask servido con gunicorn (WSGI, workers síncronos)."""
import logica  # noqa: I001

from flask import Flask, Response, request

app = Flask(__name__)
JSON = "application/json"


@app.get("/suma")
def suma():
    return Response(logica.suma(request.args.get("n", 0, type=int)), mimetype=JSON)


@app.get("/trabajo")
def trabajo():
    return Response(logica.trabajo(request.args.get("n", 0, type=int)), mimetype=JSON)


logica.listo("flask")
