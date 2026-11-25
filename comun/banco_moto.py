# -*- coding: utf-8 -*-
"""Lo común de los bancos «10 tips» contra moto: arrancar el emulador, ejecutar la AWS CLI y
escribir SALIDA.md. Sale del patrón de pruebas-10-tips-rds/correr.py, que se repetía entero en
cada banco.

    from banco_moto import Banco
    with Banco(Path(__file__).parent, "10 tips para X", puerto=5100) as b:
        b.titulo("...")
        b.aws("logs", "create-log-group", "--log-group-name", "app")

⚠️ moto emula la API, no la factura ni todos los valores por defecto de AWS: si un valor del
   emulador no coincide con la referencia de la API, NO se presenta como el de AWS.
"""
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class Banco:
    def __init__(self, aqui, nombre, puerto, region="us-east-1"):
        self.aqui, self.nombre, self.puerto = aqui, nombre, puerto
        self.ep = f"http://127.0.0.1:{puerto}"
        base = dict(os.environ, AWS_PAGER="", PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                    AWS_CLI_FILE_ENCODING="UTF-8")  # sin esto la CLI lee file:// en cp1252
        self.env = dict(base, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
                        AWS_DEFAULT_REGION=region, AWS_ENDPOINT_URL=self.ep)
        self.partes = []
        self.moto = None

    def __enter__(self):
        self.moto = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(self.puerto)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                urllib.request.urlopen(self.ep + "/moto-api/", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        urllib.request.urlopen(urllib.request.Request(self.ep + "/moto-api/reset", method="POST"))
        return self

    def __exit__(self, tipo, *_):
        self.moto.terminate()
        if tipo is None:
            import moto
            version = subprocess.run(["aws", "--version"], capture_output=True, text=True).stdout.strip()
            cab = [f"# SALIDA — {self.nombre} (demos ejecutadas)", "",
                   "Generado por `python correr.py`. **No se edita a mano.**", "",
                   f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
                   f"- {version}", f"- moto {moto.__version__} (emulador de la API de AWS)",
                   "- moto emula la API, no la factura ni todos los valores por defecto."]
            (self.aqui / "SALIDA.md").write_text("\n".join(cab + self.partes) + "\n", encoding="utf-8")
            print("→ SALIDA.md")

    def anotar(self, mostrar, txt):
        self.partes.extend(["", f"`$ {mostrar}`", "", "```", txt or "(sin salida)", "```"])
        print(f"$ {mostrar}\n{txt}\n", flush=True)

    def aws(self, *args, mostrar=None, guardar=True):
        r = subprocess.run(["aws", *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=self.env, cwd=self.aqui)
        txt = (r.stdout + r.stderr).strip()
        if guardar:
            self.anotar("aws " + (mostrar or " ".join(args)), txt)
        return txt

    def titulo(self, t):
        self.partes.extend(["", f"## {t}"])
        print(f"\n=== {t}", flush=True)

    def nota(self, t):
        self.partes.extend(["", f"> {t}"])
