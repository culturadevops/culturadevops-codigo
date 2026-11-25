# -*- coding: utf-8 -*-
"""Leccion 9 — Modulos, paquetes e imports: que corre y cuando.

El fallo: pones codigo suelto en un fichero, alguien lo importa para usar UNA funcion, y se
ejecuta todo. Por eso existe `if __name__ == "__main__"`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import inventario                      # noqa: E402


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("9.1 · __name__ vale una cosa u otra segun como llegues")
print(f"  en ESTE fichero, que estoy ejecutando:  __name__ = {__name__!r}")
print(f"  en el modulo que acabo de importar:     inventario.__name__ = {inventario.__name__!r}")
print("  Por eso el bloque `if __name__ == '__main__'` de inventario.py NO se ejecuto")
print("  al importarlo. Si lo corres directo, si.")

titulo("9.2 · Formas de importar")
print("  import inventario            -> inventario.activos()")
print("  from inventario import activos -> activos()")
print("  import inventario as inv     -> inv.activos()")
print("  ⛔ from inventario import *   -> NO: no sabes que nombres entran")
print()
print(f"  inventario.VERSION = {inventario.VERSION}")
print(f"  inventario.activos() = {[h['nombre'] for h in inventario.activos()]}")
print(f"  inventario.saturados() = {[h['nombre'] for h in inventario.saturados()]}")

titulo("9.3 · De donde salio el modulo")
print(f"  inventario.__file__ = {inventario.__file__}")
print("  Si un import trae algo que no esperabas, esta linea te lo dice en un segundo.")

titulo("9.4 · Lo que importa se ejecuta UNA vez")
import inventario as otra_vez
print(f"  importado dos veces, es el mismo objeto: {inventario is otra_vez}")
print("  Python cachea los modulos en sys.modules:")
print(f"  'inventario' in sys.modules -> {'inventario' in sys.modules}")

titulo("9.5 · Un paquete es un directorio con __init__.py")
print("  mi_paquete/")
print("      __init__.py      <- lo que se ejecuta al importar el paquete")
print("      inventario.py")
print("      despliegue.py")
print("  y entonces:  from mi_paquete import inventario")

titulo("Resumen")
print("  · el codigo suelto de un fichero corre AL IMPORTARLO")
print("  · protegelo con `if __name__ == '__main__':`")
print("  · __file__ te dice de donde salio de verdad un modulo")
print("  · nada de `import *`")
