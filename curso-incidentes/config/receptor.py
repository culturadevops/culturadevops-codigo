# Recibe los avisos de Alertmanager y los escribe, uno por linea, con la hora: es el «busca».
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class M(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        for a in d.get("alerts", []):
            print(json.dumps({"t": time.time(), "estado": a["status"], "alerta": a["labels"].get("alertname"),
                              "resumen": a.get("annotations", {}).get("resumen", "")}, ensure_ascii=False), flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
ThreadingHTTPServer(("0.0.0.0", 8001), M).serve_forever()
