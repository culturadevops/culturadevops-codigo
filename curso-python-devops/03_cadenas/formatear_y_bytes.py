# -*- coding: utf-8 -*-
"""Leccion 3 — Cadenas, f-strings y la diferencia entre texto y bytes.

Dos fallos de esta leccion salen en produccion: concatenar rutas a mano (y romperte en el otro
sistema operativo) y confundir str con bytes al leer la salida de un comando.
"""
from pathlib import Path


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("3.1 · f-strings: lo unico que necesitas para formatear")
servicio, replicas, cpu = "api", 3, 0.7351
print(f"  {servicio} tiene {replicas} replicas")
print(f"  cpu al {cpu:.1%}            <- porcentaje con 1 decimal")
print(f"  cpu al {cpu:.3f}            <- 3 decimales")
print(f"  |{servicio:<10}|{replicas:>5}|   <- alineado a izquierda y derecha")
print(f"  {1234567:,}               <- separador de miles")
print(f"  {servicio!r}                 <- !r pone las comillas (util en logs)")

titulo("3.2 · La coma del f-string que mas se usa depurando")
puertos = [80, 443]
print(f"  {puertos=}")
print(f"  {replicas * 2 = }")
print("  Poner = dentro llaves imprime la expresion Y su valor. Oro para depurar.")

titulo("3.3 · Metodos de cadena que usaras todos los dias")
linea = "  ERROR  nginx: connection refused  \n"
print(f"  original      {linea!r}")
print(f"  .strip()      {linea.strip()!r}")
print(f"  .lower()      {linea.strip().lower()!r}")
print(f"  .split(':')   {linea.strip().split(':')}")
print(f"  .startswith   {linea.strip().startswith('ERROR')}")
print(f"  'refused' in  {'refused' in linea}")

titulo("3.4 · NO concatenes rutas a mano")
mala = "/etc" + "/" + "nginx" + "/" + "nginx.conf"
buena = Path("/etc") / "nginx" / "nginx.conf"
print(f"  a mano   {mala}")
print(f"  pathlib  {buena}")
print(f"  y ademas te da las piezas:  .name={buena.name}  .suffix={buena.suffix}")
print(f"  .parent={buena.parent}")
print("  En Windows pathlib pone la barra correcta sola. A mano, no.")

titulo("3.5 · str NO es bytes")
texto = "configuración"
crudo = texto.encode("utf-8")
print(f"  texto  {texto!r}   tipo {type(texto).__name__}  longitud {len(texto)}")
print(f"  bytes  {crudo!r}   tipo {type(crudo).__name__}  longitud {len(crudo)}")
print("  La o con tilde ocupa 2 bytes: por eso las longitudes no coinciden.")
print(f"  de vuelta: {crudo.decode('utf-8')!r}")

titulo("3.6 · LA TRAMPA: decodificar con la codificacion equivocada")
try:
    crudo.decode("ascii")
except UnicodeDecodeError as e:
    print(f"  crudo.decode('ascii')  ->  UnicodeDecodeError")
    print(f"    {e}")
print("  Es el error que ves al leer un log con acentos suponiendo ascii o latin-1.")
print("  Regla: di SIEMPRE encoding='utf-8' al abrir un fichero.")

titulo("Resumen")
print("  · f-strings para todo; {x=} para depurar")
print("  · pathlib para rutas, nunca concatenar con barras")
print("  · str es texto, bytes es lo que viaja: .encode() y .decode()")
print("  · siempre encoding='utf-8' explicito")
