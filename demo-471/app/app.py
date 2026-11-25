import os

import psycopg2  # la app usa PostgreSQL en producción
from flask import Flask

app = Flask(__name__)


@app.get("/salud")
def salud():
    return {"estado": "ok", "driver": psycopg2.__version__.split()[0]}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
