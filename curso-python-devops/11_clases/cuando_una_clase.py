# -*- coding: utf-8 -*-
"""Leccion 11 — Clases, lo justo. Y cuando NO hace falta una.

Mucho codigo de sistemas se escribe con clases porque «asi se hace», y termina siendo un
diccionario con ceremonia. Aqui: cuando una clase aporta y cuando estorba.
"""
from dataclasses import dataclass, field


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("11.1 · Muchas veces te basta un diccionario")
srv = {"nombre": "web-01", "puerto": 443, "estado": "activo"}
print(f"  {srv}")
print("  Si solo guardas datos y los lees, esto ya esta bien. No hace falta mas.")

titulo("11.2 · Una clase 'a mano': mucho ruido para guardar tres cosas")


class ServidorManual:
    def __init__(self, nombre, puerto, estado="activo"):
        self.nombre = nombre
        self.puerto = puerto
        self.estado = estado

    def __repr__(self):
        return f"ServidorManual({self.nombre!r}, {self.puerto!r}, {self.estado!r})"


a = ServidorManual("web-01", 443)
print(f"  {a}")
print("  Son nueve lineas para guardar tres campos. Y falta comparar dos.")

titulo("11.3 · dataclass: lo mismo, sin el ruido")


@dataclass
class Servidor:
    nombre: str
    puerto: int = 443
    estado: str = "activo"
    etiquetas: list = field(default_factory=list)   # ⚠ NO `= []` (leccion 6)

    @property
    def url(self):
        esquema = "https" if self.puerto == 443 else "http"
        return f"{esquema}://{self.nombre}:{self.puerto}"

    def esta_vivo(self):
        return self.estado == "activo"


s1 = Servidor("web-01")
s2 = Servidor("web-01")
s3 = Servidor("db-01", puerto=5432, estado="parado")
print(f"  s1 = {s1}")
print(f"  s3 = {s3}")
print(f"  s1 == s2  ->  {s1 == s2}   <- dataclass te da la comparacion gratis")
print(f"  s1.url        {s1.url}     <- @property: se usa sin parentesis")
print(f"  s3.url        {s3.url}")
print(f"  s3.esta_vivo()  {s3.esta_vivo()}")

titulo("11.4 · Por que field(default_factory=list) y no `= []`")
print("  Es el MISMO fallo de la leccion 6: un valor por omision mutable")
print("  se compartiria entre TODAS las instancias.")
s1.etiquetas.append("produccion")
print(f"  s1.etiquetas = {s1.etiquetas}")
print(f"  s2.etiquetas = {s2.etiquetas}   <- vacia, como debe ser")
print("  Con `= []` dataclass directamente se niega a definir la clase.")

titulo("11.5 · Cuando SI vale la pena una clase")
print("  · cuando los datos y las operaciones sobre ellos van juntos")
print("  · cuando quieres validar al construir (un puerto fuera de rango)")
print("  · cuando vas a tener muchas instancias y quieres comparar u ordenar")
print()
print("  Cuando NO:")
print("  · si es solo un saco de campos que lees una vez -> diccionario")
print("  · si la clase solo tiene metodos y ningun estado -> funciones sueltas")

titulo("11.6 · Ordenar una lista de objetos")
hosts = [Servidor("web-02", 80), Servidor("web-01"), Servidor("db-01", 5432, "parado")]
for h in sorted(hosts, key=lambda x: x.nombre):
    print(f"  {h.nombre:<8} {h.url:<24} vivo={h.esta_vivo()}")
vivos = [h.nombre for h in hosts if h.esta_vivo()]
print(f"  vivos: {vivos}")

titulo("Resumen")
print("  · @dataclass te da __init__, __repr__ y __eq__ gratis")
print("  · field(default_factory=list) para los mutables")
print("  · @property para lo calculado que se lee como un atributo")
print("  · si no hay comportamiento, un diccionario es mejor que una clase")
