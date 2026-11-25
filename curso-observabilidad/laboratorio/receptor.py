# -*- coding: utf-8 -*-
"""Recibe los avisos de Alertmanager y los apunta, para poder enseñar el agrupado."""
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class M(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(n) or b"{}")
        print("%s  AVISO recibido: %d alerta(s) en un solo mensaje  [%s]"
              % (time.strftime("%H:%M:%S"), len(d.get("alerts", [])),
                 d.get("groupLabels", {}).get("alertname", "?")), flush=True)
        for a in d.get("alerts", []):
            print("    - %s  %s" % (a["labels"].get("alertname"),
                                    a.get("annotations", {}).get("resumen", "")[:60]), flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
ThreadingHTTPServer(("0.0.0.0", 8001), M).serve_forever()
