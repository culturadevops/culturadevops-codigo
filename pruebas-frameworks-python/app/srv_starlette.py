# -*- coding: utf-8 -*-
"""Starlette (la base de FastAPI) servido con uvicorn. Rutas con `def`: Starlette las manda al threadpool, igual que FastAPI."""
import logica  # noqa: I001

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

JSON = "application/json"


def suma(request):
    return Response(logica.suma(int(request.query_params.get("n", 0))), media_type=JSON)


def trabajo(request):
    return Response(logica.trabajo(int(request.query_params.get("n", 0))), media_type=JSON)


@asynccontextmanager
async def vida(_app):
    logica.listo("starlette")
    yield


app = Starlette(routes=[Route("/suma", suma), Route("/trabajo", trabajo)], lifespan=vida)
