from flask import Flask
from waitress import serve

app = Flask(__name__)


@app.get('/')
def inicio():
    return 'ok'


def run():
    serve(app, host='0.0.0.0', port=8080)
