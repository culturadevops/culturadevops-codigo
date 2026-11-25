# 715 · PEP 686: open() sin encoding. Se ejecuta en WINDOWS (es donde cambia): Python 3.14.10 frente a 3.15.2.
# Escribe un archivo en un directorio temporal y lo lee como lo haría otra herramienta: en UTF-8.
import locale
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")  # solo la consola de esta demo; open() sigue con su valor por defecto
d = tempfile.mkdtemp(prefix="v715-")
ruta = os.path.join(d, "config.txt")
with open(ruta, "w") as f:  # sin encoding: depende de la versión
    f.write("año=2026\n")
crudo = open(ruta, "rb").read()
print(f"Python {sys.version.split()[0]} · utf8_mode={sys.flags.utf8_mode} · open() usa {locale.getpreferredencoding(False)}")
print(f"bytes escritos: {crudo!r}")
try:
    print("leído como UTF-8:", crudo.decode("utf-8").strip())
except UnicodeDecodeError as e:
    print("leído como UTF-8: UnicodeDecodeError:", e.reason)
os.remove(ruta)
os.rmdir(d)
