# -*- coding: utf-8 -*-
"""Sanic con su propio servidor (no usa uvicorn ni gunicorn). Rutas `async def`, como en su documentación: Sanic no tiene
threadpool automático, el cálculo corre en el bucle de eventos."""
import logica  # noqa: I001

from sanic import Sanic
from sanic.response import raw

app = Sanic("banco")
JSON = "application/json"


@app.get("/suma")
async def suma(request):
    return raw(logica.suma(int(request.args.get("n", 0))).encode(), content_type=JSON)


@app.get("/trabajo")
async def trabajo(request):
    return raw(logica.trabajo(int(request.args.get("n", 0))).encode(), content_type=JSON)


@app.after_server_start
async def listo(_app):
    logica.listo("sanic")
