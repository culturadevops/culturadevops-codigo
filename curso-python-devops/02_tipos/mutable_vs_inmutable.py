# -*- coding: utf-8 -*-
"""Leccion 2 — Tipos, y la unica distincion que de verdad muerde: mutable o inmutable.

El fallo: pasas una lista a una funcion, la funcion la modifica, y tu lista de fuera cambia.
Nadie te avisa. En un script que recorre servidores, eso es un incidente.
"""


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("2.1 · Los tipos que vas a usar de verdad")
for v in (42, 3.5, "texto", True, None, [1, 2], (1, 2), {"a": 1}, {1, 2}):
    print(f"  {str(v):<14} -> {type(v).__name__}")

titulo("2.2 · Inmutable: el numero y la cadena no cambian, se sustituyen")
a = 10
b = a
b += 5
print(f"  a = 10; b = a; b += 5   ->   a={a}  b={b}   (a NO cambio)")

s = "hola"
t = s
t += " mundo"
print(f"  s = 'hola'; t = s; t += ' mundo'  ->  s={s!r}  t={t!r}")

titulo("2.3 · Mutable: LA MISMA lista con dos nombres")
lista_a = ["web-01", "web-02"]
lista_b = lista_a          # esto NO copia: es otro nombre para lo mismo
lista_b.append("web-03")
print(f"  lista_a = {lista_a}")
print(f"  lista_b = {lista_b}")
print(f"  son el mismo objeto?  id(lista_a)==id(lista_b)  ->  {lista_a is lista_b}")
print("  Anadiste a lista_b y aparecio en lista_a. Ese es el fallo.")

titulo("2.4 · Como se copia de verdad")
original = ["web-01", "web-02"]
copia = list(original)      # o original.copy(), o original[:]
copia.append("web-03")
print(f"  original = {original}")
print(f"  copia    = {copia}")
print(f"  distintos objetos:  {original is not copia}")

titulo("2.5 · LA TRAMPA DE LA COPIA SUPERFICIAL")
# list() copia la lista de fuera, pero NO lo que hay dentro.
servidores = [{"nombre": "web-01", "puertos": [80]}]
copia_superficial = list(servidores)
copia_superficial[0]["puertos"].append(443)
print(f"  servidores        = {servidores}")
print(f"  copia_superficial = {copia_superficial}")
print("  El diccionario de dentro es EL MISMO. Para copiar en profundidad:")
import copy as _copy
honda = _copy.deepcopy(servidores)
honda[0]["puertos"].append(8080)
print(f"  tras deepcopy y anadir 8080 a la copia:")
print(f"    servidores = {servidores}")
print(f"    honda      = {honda}")

titulo("2.6 · `is` no es `==`")
x = [1, 2, 3]
y = [1, 2, 3]
print(f"  x == y  ->  {x == y}   (mismo CONTENIDO)")
print(f"  x is y  ->  {x is y}   (mismo OBJETO)")
print("  Usa `is` solo con None, True y False. Para todo lo demas, `==`.")

titulo("Resumen")
print("  · inmutables: int, float, str, bool, tuple  -> se sustituyen")
print("  · mutables:   list, dict, set               -> se modifican en su sitio")
print("  · asignar NO copia: crea otro nombre para el mismo objeto")
print("  · list() copia un nivel; copy.deepcopy() copia todo")
print("  · `is` compara identidad, `==` compara contenido")
