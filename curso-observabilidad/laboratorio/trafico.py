# -*- coding: utf-8 -*-
"""Tráfico continuo para el laboratorio: mantiene datos vivos en las gráficas."""
import random, threading, time, urllib.request
def pide(u):
    try: urllib.request.urlopen(u, timeout=8).read()
    except Exception: pass
def rapidas():
    while True:
        p = random.choice(["ES", "PT", "FR", "IT", "ES", "ES", "XX"])  # ~14% fallan
        pide("http://localhost:8000/pedido?pais=%s" % p)
        time.sleep(random.uniform(0.2, 0.6))
def lentas():
    while True:
        pide("http://localhost:8000/buscar")
        time.sleep(random.uniform(4, 8))
for f in (rapidas, rapidas, lentas):
    threading.Thread(target=f, daemon=True).start()
while True:
    time.sleep(60)
