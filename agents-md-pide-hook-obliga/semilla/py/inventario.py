"""Inventario sencillo de artículos en memoria."""
import os
import json
from dataclasses import dataclass


@dataclass
class Articulo:
    nombre: str
    cantidad: int
    precio: float


def desde_json(texto: str) -> list[Articulo]:
    datos = json.loads(texto)
    return [Articulo(**d) for d in datos]


def agotados(items: list[Articulo]) -> list[Articulo]:
    return [a for a in items if a.cantidad == 0]
