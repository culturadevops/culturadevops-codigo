# -*- coding: utf-8 -*-
"""Leccion 5 — Condicionales y bucles, y el fallo silencioso al recorrer.

Modificar una lista mientras la recorres no da error: da un resultado MAL. Es de los pocos
fallos que pasan las pruebas y llegan a produccion.
"""


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("5.1 · Lo que Python considera falso")
for v in (0, 0.0, "", [], {}, set(), None, False):
    print(f"  bool({v!r:<8}) -> {bool(v)}")
print("  Por eso `if lista:` ya significa 'si la lista NO esta vacia'.")
print("  ⚠ Y por eso `if x:` NO es lo mismo que `if x is not None:` cuando x puede ser 0.")

titulo("5.2 · LA TRAMPA: borrar mientras recorres")
servidores = ["web-01", "web-02", "parado-01", "parado-02", "db-01"]
copia = list(servidores)
for s in copia:
    if s.startswith("parado"):
        copia.remove(s)
print(f"  original  ['web-01','web-02','parado-01','parado-02','db-01']")
print(f"  resultado {copia}")
print("  Quedo 'parado-02'. Al borrar 'parado-01' todo se corrio una posicion")
print("  y el bucle se salto el siguiente. NO dio error. Solo salio mal.")

bien = [s for s in servidores if not s.startswith("parado")]
print(f"  la forma correcta (comprension): {bien}")

titulo("5.3 · enumerate y zip: los dos que sustituyen al indice a mano")
hosts = ["web-01", "web-02"]
estados = ["activo", "parado"]
for i, h in enumerate(hosts, start=1):
    print(f"  {i}. {h}")
for h, e in zip(hosts, estados):
    print(f"  {h} -> {e}")
print("  ⚠ zip PARA en la lista mas corta, y no avisa. Si las longitudes")
print("    deben coincidir, usa zip(..., strict=True) (Python 3.10+).")
try:
    list(zip([1, 2, 3], [1, 2], strict=True))
except ValueError as e:
    print(f"    con strict=True  ->  ValueError: {e}")

titulo("5.4 · for/else: el que casi nadie conoce y aqui viene bien")
buscado = "db-02"
for h in hosts:
    if h == buscado:
        print(f"  encontrado {h}")
        break
else:
    print(f"  {buscado!r} no esta en la lista   <- el else del for corre si NO hubo break")

titulo("5.5 · Recorrer un diccionario")
srv = {"nombre": "web-01", "puerto": 443, "estado": "activo"}
for clave, valor in srv.items():
    print(f"  {clave:<8} = {valor}")

titulo("Resumen")
print("  · no modifiques una lista mientras la recorres: filtra a una nueva")
print("  · enumerate() para el indice, zip() para ir en paralelo")
print("  · zip se para en la mas corta: strict=True si eso es un fallo")
print("  · for/else corre el else cuando NO hubo break")
