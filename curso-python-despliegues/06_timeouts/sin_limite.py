# -*- coding: utf-8 -*-
"""Leccion 6 — Timeouts: por defecto, Python espera para siempre."""
import socket
import threading
import time
import urllib.request


def servidor(atender):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen()
    threading.Thread(target=lambda: atender(s), daemon=True).start()
    return f"http://127.0.0.1:{s.getsockname()[1]}/"


def mudo(s):
    """Acepta la conexion y no contesta nunca."""
    guardadas = []
    while True:
        c, _ = s.accept()
        guardadas.append(c)


def gotero(s):
    """Contesta... un byte cada 0,3 s."""
    while True:
        c, _ = s.accept()
        c.recv(4096)                                  # leer la peticion antes de cerrar
        c.sendall(b"HTTP/1.0 200 OK\r\nContent-Length: 10\r\n\r\n")
        for _ in range(10):
            time.sleep(0.3)
            c.sendall(b"x")
        c.shutdown(socket.SHUT_WR)
        c.close()


print("== 6.1 · El valor por defecto ==")
print(f"  socket.getdefaulttimeout() -> {socket.getdefaulttimeout()}   <- sin limite")

url = servidor(mudo)
print()
print("== 6.2 · LA TRAMPA: urlopen sin timeout contra un servicio colgado ==")
resultado = {}


def sin_timeout():
    urllib.request.urlopen(url).read()
    resultado["fin"] = True


h = threading.Thread(target=sin_timeout, daemon=True)
h.start()
h.join(3)
print(f"  a los 3 s: sigue esperando = {h.is_alive()}   (y seguiria horas)")

t0 = time.perf_counter()
try:
    urllib.request.urlopen(url, timeout=1).read()
except (TimeoutError, OSError) as e:
    print(f"  con timeout=1: {type(e).__name__} a los {time.perf_counter() - t0:.1f} s")

print()
print("== 6.3 · LA TRAMPA 2: el timeout es por espera, no total ==")
url = servidor(gotero)
t0 = time.perf_counter()
cuerpo = urllib.request.urlopen(url, timeout=1).read()
print(f"  timeout=1, pero la llamada duro {time.perf_counter() - t0:.1f} s y NO fallo "
      f"({len(cuerpo)} bytes)")
print("  Cada byte llega antes de 1 s, asi que el reloj se reinicia cada vez.")


def con_plazo(url, plazo):
    """Plazo TOTAL: se lee a trozos y se mira el reloj."""
    limite = time.monotonic() + plazo
    with urllib.request.urlopen(url, timeout=plazo) as r:
        datos = b""
        while chunk := r.read(1):
            datos += chunk
            if time.monotonic() > limite:
                raise TimeoutError(f"plazo total de {plazo} s superado")
    return datos


t0 = time.perf_counter()
try:
    con_plazo(url, 1)
except TimeoutError as e:
    print(f"  con plazo total: TimeoutError a los {time.perf_counter() - t0:.1f} s ({e})")
