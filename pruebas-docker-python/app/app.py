# La app del vídeo 153: una API Flask mínima pero real (dos rutas, un JSON).
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def raiz():
    return jsonify(app="notas-api", ok=True)


@app.get("/salud")
def salud():
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
