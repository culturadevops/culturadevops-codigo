# -*- coding: utf-8 -*-
"""Leccion 8 — Excepciones, y por que un `except:` pelado es un fallo, no un estilo.

Un except sin tipo se traga TODO: incluido el Ctrl+C con el que intentas parar el script y el
SystemExit con el que intenta salir. Es la forma mas rapida de escribir algo que no se puede
matar ni depurar.
"""
import sys


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("8.1 · try / except / else / finally")
def dividir(a, b):
    try:
        r = a / b
    except ZeroDivisionError:
        return "division por cero"
    else:
        return f"resultado {r}"          # solo si NO hubo excepcion
    finally:
        pass                             # SIEMPRE, haya fallado o no


print(f"  dividir(10, 2) -> {dividir(10, 2)}")
print(f"  dividir(10, 0) -> {dividir(10, 0)}")

titulo("8.2 · Captura el tipo que esperas, no todos")
datos = {"host": "web-01"}
try:
    datos["puerto"]
except KeyError as e:
    print(f"  KeyError capturado: falta la clave {e}")
try:
    int("no-es-un-numero")
except ValueError as e:
    print(f"  ValueError capturado: {e}")
try:
    open("/no/existe/de/verdad.conf")
except FileNotFoundError as e:
    print(f"  FileNotFoundError capturado: {e.strerror}")
print("  Varios a la vez:  except (KeyError, ValueError) as e:")

titulo("8.3 · LA TRAMPA: el except pelado")
print("  Esto:")
print("      try:  algo()")
print("      except:  pass")
print()
print("  se traga TAMBIEN:")
for exc in (KeyboardInterrupt, SystemExit, MemoryError):
    print(f"    · {exc.__name__:<18} -> {'tu Ctrl+C' if exc is KeyboardInterrupt else 'la salida del proceso' if exc is SystemExit else 'te quedaste sin memoria'}")
print()
print("  KeyboardInterrupt y SystemExit NO heredan de Exception, precisamente")
print("  para que `except Exception` no los pille:")
print(f"    issubclass(KeyboardInterrupt, Exception) -> {issubclass(KeyboardInterrupt, Exception)}")
print(f"    issubclass(ValueError, Exception)        -> {issubclass(ValueError, Exception)}")
print("  Si tienes que capturar amplio, captura `Exception`, nunca pelado.")

titulo("8.4 · No te comas el error: relanza con contexto")


class ErrorDeConfiguracion(Exception):
    """Un error nuestro, con el fichero que lo causo."""


def cargar(ruta):
    try:
        return int("puerto-mal")
    except ValueError as e:
        raise ErrorDeConfiguracion(f"{ruta}: el puerto no es un numero") from e


try:
    cargar("/etc/app.conf")
except ErrorDeConfiguracion as e:
    print(f"  {type(e).__name__}: {e}")
    print(f"  causa original: {type(e.__cause__).__name__}: {e.__cause__}")
print("  `raise ... from e` conserva la causa. Sin el `from`, la pierdes.")

titulo("8.5 · El codigo de salida, que es lo que mira tu tuberia")
print("  sys.exit(0) -> todo bien      (lo que espera CI)")
print("  sys.exit(1) -> algo fallo")
print("  sys.exit(2) -> uso incorrecto (lo que usa argparse)")
print("  Si tu script solo imprime 'ERROR' y sale con 0, CI lo da por bueno.")
print(f"  (este proceso saldra con 0; ahora mismo sys.argv[0]={sys.argv[0].split(chr(92))[-1]})")

titulo("Resumen")
print("  · captura el tipo concreto; `except Exception` si tienes que ser amplio")
print("  · `except:` pelado se traga el Ctrl+C: es un fallo")
print("  · `raise MiError(...) from e` conserva la causa")
print("  · finally para soltar lo que hayas cogido")
print("  · el codigo de salida es lo que lee CI, no tu mensaje")
