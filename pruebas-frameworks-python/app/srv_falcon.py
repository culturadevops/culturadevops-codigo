# -*- coding: utf-8 -*-
"""Falcon (WSGI) servido con gunicorn (workers síncronos)."""
import logica  # noqa: I001

import falcon

JSON = "application/json"


class Suma:
    def on_get(self, req, resp):
        resp.content_type = JSON
        resp.text = logica.suma(req.get_param_as_int("n", default=0))


class Trabajo:
    def on_get(self, req, resp):
        resp.content_type = JSON
        resp.text = logica.trabajo(req.get_param_as_int("n", default=0))


app = falcon.App()
app.add_route("/suma", Suma())
app.add_route("/trabajo", Trabajo())
logica.listo("falcon")
