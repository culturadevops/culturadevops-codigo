# -*- coding: utf-8 -*-
"""Leccion 5 — Reintentos: cuales se reintentan, cuantas veces, y cuanto se espera."""
import random
import time

TRANSITORIOS = (ConnectionError, TimeoutError)


def reintentar(fn, intentos=5, base=0.1, tope=2.0, reintentar_si=TRANSITORIOS,
               azar=random.random):
    """Espera exponencial con jitter completo. Solo reintenta lo transitorio."""
    for n in range(1, intentos + 1):
        try:
            return fn()
        except reintentar_si as e:
            if n == intentos:
                raise
            espera = azar() * min(tope, base * 2 ** (n - 1))
            print(f"    intento {n}: {type(e).__name__} -> espero {espera * 1000:.0f} ms")
            time.sleep(espera)


print("== 5.1 · Un servicio que falla dos veces y luego contesta ==")
llamadas = {"n": 0}


def registro_de_imagenes():
    llamadas["n"] += 1
    if llamadas["n"] <= 2:
        raise ConnectionError("conexion rechazada")
    return "imagen app:v2 descargada"


print(f"  -> {reintentar(registro_de_imagenes, azar=random.Random(7).random)}")

print()
print("== 5.2 · LA TRAMPA: reintentarlo TODO ==")


def leer_config():
    raise ValueError("replicas='cinco' no es un numero")


t0 = time.perf_counter()
try:
    reintentar(leer_config, reintentar_si=Exception, azar=lambda: 1.0)
except ValueError as e:
    print(f"  ValueError tras 5 intentos y {time.perf_counter() - t0:.1f} s: {e}")
print("  Un error de config no se arregla esperando. Solo se retrasa el aviso.")
t0 = time.perf_counter()
try:
    reintentar(leer_config)
except ValueError as e:
    print(f"  solo transitorios: ValueError al primer intento ({(time.perf_counter() - t0) * 1000:.0f} ms)")

print()
print("== 5.3 · LA TRAMPA: reintentar algo que NO es idempotente ==")


class Servidor:
    """Registra la release... y la respuesta se pierde por el camino."""

    def __init__(self):
        self.releases, self.vistas, self.perdidas = [], set(), 1

    def registrar(self, version, clave=None):
        if clave is not None and clave in self.vistas:
            return "ya registrada"
        self.releases.append(version)                  # el trabajo SI se hizo
        if clave is not None:
            self.vistas.add(clave)
        if self.perdidas:
            self.perdidas -= 1
            raise TimeoutError("sin respuesta")        # pero tu no te enteras
        return "registrada"


s = Servidor()
reintentar(lambda: s.registrar("v2"), azar=lambda: 0.0)
print(f"  sin clave:        releases = {s.releases}")
s = Servidor()
reintentar(lambda: s.registrar("v2", clave="despliegue-2026-0042"), azar=lambda: 0.0)
print(f"  con clave de idempotencia: releases = {s.releases}")
print("  Un timeout NO significa que no se hizo. Significa que no sabes.")

print()
print("== 5.4 · Por que el azar (jitter): 5 clientes caen a la vez ==")
for nombre, azar in (("sin jitter", lambda: 1.0), ("con jitter", random.Random(3).random)):
    momentos = []
    for cliente in range(5):
        t = 0.0
        for n in range(1, 4):
            t += azar() * min(2.0, 0.1 * 2 ** (n - 1))
        momentos.append(round(t * 1000))
    print(f"  {nombre}: el 3er reintento de cada cliente llega en ms {momentos}")
print("  Sin azar, todos vuelven al mismo milisegundo y lo vuelven a tumbar.")
