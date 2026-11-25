# ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
import sqlite3
import subprocess

from flask import Flask, request

from consultas import buscar_productos

app = Flask(__name__)


def db():
    return sqlite3.connect("tienda.db")


@app.route("/usuario")
def usuario():
    # V1: inyección SQL
    id_ = request.args.get("id")
    return str(db().execute("SELECT nombre FROM usuarios WHERE id = " + id_).fetchall())


@app.route("/ping")
def ping():
    # V2: inyección de comandos
    host = request.args.get("host")
    return subprocess.run("ping -c 1 " + host, shell=True, capture_output=True, text=True).stdout


@app.route("/buscar")
def buscar():
    # V3: inyección SQL a través de otro archivo
    return str(buscar_productos(db(), request.args.get("q")))


@app.route("/usuario_seguro")
def usuario_seguro():
    # S1: consulta con parámetros: segura
    return str(db().execute("SELECT nombre FROM usuarios WHERE id = ?", (request.args.get("id"),)).fetchall())


@app.route("/pedido")
def pedido():
    # S2: el id se convierte a entero: seguro
    id_ = int(request.args.get("id"))
    return str(db().execute("SELECT total FROM pedidos WHERE id = " + str(id_)).fetchall())
