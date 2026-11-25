# -*- coding: utf-8 -*-
"""Leccion 4 — Listas, diccionarios, conjuntos y tuplas: cual y por que.

El fallo de esta leccion no se ve con 10 elementos. Se ve con 10.000, cuando el script que
tardaba un segundo tarda un minuto porque buscas en una lista lo que deberia ser un diccionario.
"""
import timeit


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("4.1 · Las cuatro, en una linea cada una")
print("  lista  [..]  ordenada, repetible, mutable      -> una secuencia de cosas")
print("  tupla  (..)  ordenada, repetible, INMUTABLE    -> un registro fijo")
print("  dict   {k:v} clave -> valor, mutable           -> un indice")
print("  set    {..}  sin orden, SIN REPETIDOS          -> pertenencia y diferencias")

titulo("4.2 · Diccionario: leer sin que reviente")
srv = {"nombre": "web-01", "puerto": 443}
print(f"  srv['nombre']                  -> {srv['nombre']}")
print(f"  srv.get('region')              -> {srv.get('region')}")
print(f"  srv.get('region', 'us-east-1') -> {srv.get('region', 'us-east-1')}")
try:
    srv["region"]
except KeyError as e:
    print(f"  srv['region']                  -> KeyError: {e}")
print("  En un script desatendido, .get() con valor por omision te ahorra la traza.")

titulo("4.3 · Conjuntos: la herramienta para comparar inventarios")
declarados = {"web-01", "web-02", "web-03", "db-01"}
vivos = {"web-01", "web-03", "db-01", "cache-01"}
print(f"  declarados  {sorted(declarados)}")
print(f"  vivos       {sorted(vivos)}")
print(f"  declarados - vivos  = {sorted(declarados - vivos)}   <- deberian estar y NO estan")
print(f"  vivos - declarados  = {sorted(vivos - declarados)}   <- estan y nadie los declaro")
print(f"  interseccion        = {sorted(declarados & vivos)}")
print("  Esas dos restas son media herramienta de auditoria, en dos lineas.")

titulo("4.4 · LA MEDIDA: buscar en una lista contra buscar en un conjunto")
N = 200_000
lista = [f"host-{i}" for i in range(N)]
conjunto = set(lista)
diccionario = {h: i for i, h in enumerate(lista)}
objetivo = f"host-{N - 1}"          # el peor caso para la lista: el ultimo

# ⚠ Una sola busqueda en un conjunto tarda ~1 microsegundo: casi lo que resuelve el reloj.
# Medir UNA vez da un numero distinto en cada ejecucion. Por eso se repite REPS veces y
# se divide: asi los dos lados quedan muy por encima de la resolucion del reloj.
REPS = 300
t_lista = timeit.timeit(lambda: objetivo in lista, number=REPS) / REPS * 1e9
t_set = timeit.timeit(lambda: objetivo in conjunto, number=REPS * 100) / (REPS * 100) * 1e9
t_dict = timeit.timeit(lambda: diccionario[objetivo], number=REPS * 100) / (REPS * 100) * 1e9

print(f"  buscando {objetivo!r} entre {N:,} elementos (media de muchas repeticiones):")
print(f"    en una lista        {t_lista:>10,.0f} ns   <- recorre uno a uno")
print(f"    en un conjunto      {t_set:>10,.0f} ns")
print(f"    en un diccionario   {t_dict:>10,.0f} ns")
if t_set > 0:
    print(f"    la lista es ~{t_lista / t_set:,.0f} veces mas lenta que el conjunto")
print("  Con 10 elementos da igual. Con 200.000 es la diferencia entre")
print("  un script de 1 segundo y uno de varios minutos.")

titulo("4.5 · Comprensiones: filtrar y transformar en una linea")
servidores = [
    {"nombre": "web-01", "estado": "activo", "cpu": 0.91},
    {"nombre": "web-02", "estado": "parado", "cpu": 0.00},
    {"nombre": "db-01", "estado": "activo", "cpu": 0.42},
]
nombres = [s["nombre"] for s in servidores]
saturados = [s["nombre"] for s in servidores if s["cpu"] > 0.8]
por_nombre = {s["nombre"]: s["estado"] for s in servidores}
print(f"  todos      {nombres}")
print(f"  saturados  {saturados}")
print(f"  indice     {por_nombre}")

titulo("4.6 · Tupla: cuando NO quieres que cambie")
punto = ("web-01", 443)
print(f"  punto = {punto}")
try:
    punto[1] = 80
except TypeError as e:
    print(f"  punto[1] = 80  ->  TypeError: {e}")
print("  Y por eso una tupla SI puede ser clave de un diccionario, y una lista no:")
metricas = {("web-01", "cpu"): 0.91, ("web-01", "ram"): 0.55}
print(f"  metricas[('web-01','cpu')] = {metricas[('web-01', 'cpu')]}")

titulo("Resumen")
print("  · dict cuando busques por clave; set cuando preguntes '¿esta?'")
print("  · buscar en una lista recorre TODO: medido arriba")
print("  · .get(clave, por_omision) en vez de corchetes")
print("  · restar conjuntos es una auditoria en dos lineas")
print("  · tupla para lo que no debe cambiar, y para claves compuestas")
