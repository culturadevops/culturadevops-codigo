"""La misma tienda, con los 4 fallos arreglados (demo de cultura-devops)."""
import ipaddress
import os
import sqlite3
import subprocess
from pathlib import Path

import yaml
from flask import Flask, abort, request

app = Flask(__name__)
DB = "tienda.db"
FACTURAS = Path("/srv/facturas").resolve()
# Arreglo 4: la clave viene del entorno (en el pipeline, de un gestor de secretos)
STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]


@app.route("/producto")
def producto():
    nombre = request.args.get("nombre", "")
    con = sqlite3.connect(DB)
    # Arreglo 1: consulta con parámetros
    filas = con.execute("SELECT id, nombre, precio FROM productos WHERE nombre = ?", (nombre,)).fetchall()
    return {"productos": filas}


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # Arreglo 2: se valida que sea una IP y no hay shell
    try:
        ip = str(ipaddress.ip_address(host))
    except ValueError:
        abort(400)
    salida = subprocess.check_output(["ping", "-c", "1", ip])  # nosec B603 B607
    return salida


@app.route("/factura")
def factura():
    archivo = request.args.get("archivo", "")
    # Arreglo 3: la ruta final tiene que quedar dentro de FACTURAS
    ruta = (FACTURAS / archivo).resolve()
    if not ruta.is_relative_to(FACTURAS):
        abort(404)
    return ruta.read_text()


@app.route("/config", methods=["POST"])
def config():
    datos = yaml.safe_load(request.data)
    return {"ok": bool(datos)}
