# -*- coding: utf-8 -*-
"""Leccion 6 — Funciones, y el clasico que muerde una vez en la vida: el mutable por omision.

Un valor por omision se evalua UNA vez, al definir la funcion. Si es una lista, todas las
llamadas comparten la MISMA lista.
"""


def titulo(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


titulo("6.1 · Argumentos: posicionales, con nombre y por omision")


def desplegar(servicio, replicas=1, region="us-east-1"):
    return f"{servicio} x{replicas} en {region}"


print(f"  desplegar('api')                          -> {desplegar('api')}")
print(f"  desplegar('api', 3)                       -> {desplegar('api', 3)}")
print(f"  desplegar('api', region='eu-west-1')      -> {desplegar('api', region='eu-west-1')}")
print("  Los que tienen nombre se leen solos dentro de seis meses. Usalos.")

titulo("6.2 · EL CLASICO: lista como valor por omision")


def anadir_mal(host, lista=[]):        # ⛔ NUNCA hagas esto
    lista.append(host)
    return lista


print(f"  anadir_mal('web-01')  -> {anadir_mal('web-01')}")
print(f"  anadir_mal('web-02')  -> {anadir_mal('web-02')}")
print(f"  anadir_mal('web-03')  -> {anadir_mal('web-03')}")
print("  Esperabas ['web-02'] en la segunda. Salio acumulado.")
print("  La lista por omision se creo UNA vez, al definir la funcion.")


def anadir_bien(host, lista=None):     # ✅ asi
    if lista is None:
        lista = []
    lista.append(host)
    return lista


print(f"  anadir_bien('web-01') -> {anadir_bien('web-01')}")
print(f"  anadir_bien('web-02') -> {anadir_bien('web-02')}")

titulo("6.3 · *args y **kwargs: cuando no sabes cuantos vienen")


def registrar(nivel, *mensajes, **campos):
    extra = " ".join(f"{k}={v}" for k, v in campos.items())
    return f"[{nivel}] {' '.join(mensajes)} {extra}".strip()


print(f"  {registrar('INFO', 'arranque', 'ok')}")
print(f"  {registrar('ERROR', 'fallo al conectar', host='db-01', intento=3)}")

titulo("6.4 · Devolver varias cosas (es una tupla)")


def analizar(hosts):
    activos = [h for h in hosts if not h.startswith("parado")]
    return len(activos), len(hosts) - len(activos)


vivos, caidos = analizar(["web-01", "parado-01", "db-01"])
print(f"  vivos={vivos}  caidos={caidos}")

titulo("6.5 · Anotaciones de tipo: documentacion que tu editor lee")


def escalar(servicio: str, replicas: int = 1) -> str:
    return f"{servicio} -> {replicas}"


print(f"  {escalar('api', 3)}")
print("  Python NO las comprueba al ejecutar, pero tu editor y mypy si.")
print("  En un script que va a leer otro, valen su peso en oro.")

titulo("Resumen")
print("  · valor por omision mutable: usa None y crealo dentro")
print("  · llama con nombre lo que no sea obvio")
print("  · *args y **kwargs para lo variable")
print("  · anota los tipos: es documentacion que no se queda vieja en silencio")
