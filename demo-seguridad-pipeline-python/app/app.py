"""Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops).
No la despliegues: es para que los escáneres la encuentren."""
import os
import sqlite3
import subprocess

import yaml
from flask import Flask, request

app = Flask(__name__)
DB = "tienda.db"
FACTURAS = "/srv/facturas"
# Fallo 4: una clave pegada en el código
STRIPE_API_KEY = "CLAVE_STRIPE_FALSA_DE_EJEMPLO"
password = "admin123"


@app.route("/producto")
def producto():
    nombre = request.args.get("nombre", "")
    con = sqlite3.connect(DB)
    # Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
    filas = con.execute(f"SELECT id, nombre, precio FROM productos WHERE nombre = '{nombre}'").fetchall()
    return {"productos": filas}


@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")
    # Fallo 2: inyección de comandos (shell=True con texto del usuario)
    salida = subprocess.check_output(f"ping -c 1 {host}", shell=True)
    return salida


@app.route("/factura")
def factura():
    archivo = request.args.get("archivo", "")
    # Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
    with open(os.path.join(FACTURAS, archivo)) as f:
        return f.read()


@app.route("/config", methods=["POST"])
def config():
    # Extra: yaml.load sin Loader seguro
    datos = yaml.load(request.data, Loader=yaml.Loader)
    return {"ok": bool(datos)}
