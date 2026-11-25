# -*- coding: utf-8 -*-
"""Monitor de disponibilidad en Python con alertas a un webhook de Discord (cultura-devops 799).
asyncio + httpx. Una tarea por sitio, cada una con su propio ritmo; un solo «cartero» manda los avisos.

    python monitor.py estados      # umbral de fallos seguidos + avisar solo al cambiar de estado
    python monitor.py ingenuo      # avisa en cada revisión que falla
    python monitor.py rondas       # el error de hacerlo por rondas con gather
    python monitor.py sin-timeout  # urllib sin timeout contra un sitio que tarda 3 s
    python monitor.py entorno      # sin DISCORD_WEBHOOK_URL no arranca

DISCORD_WEBHOOK_URL apunta al Discord FALSO del banco: nada se envía a Discord de verdad.
"""
import asyncio
import datetime as dt
import os
import socket
import sys
import time
import urllib.request

import httpx

SITIOS = {"web": "http://cd799-sitios:8001/", "api": "http://cd799-api:8000/",
          "pagos": "http://cd799-sitios:8002/", "lento": "http://cd799-sitios:8003/"}
INTERVALO = 1.0     # cada cuánto se revisa cada sitio
TIMEOUT = 2.0       # lo máximo que se espera una respuesta
UMBRAL = 3          # fallos seguidos antes de declarar CAÍDO
SEGUNDOS = float(os.environ.get("SEGUNDOS", "20"))

T0 = time.monotonic()
ROJO, VERDE = 0xE74C3C, 0x2ECC71


def t():
    return f"{time.monotonic() - T0:5.1f} s"


def motivo_conexion(e):
    """httpx envuelve el error del sistema: se recorre la cadena de causas hasta encontrarlo."""
    c = e
    while c is not None:
        if isinstance(c, ConnectionRefusedError):
            return "conexión rechazada"
        if isinstance(c, socket.gaierror):
            return "el nombre no resuelve (DNS)"
        c = c.__cause__ or c.__context__
    return f"no conecta: {e}"


async def esperar_turno(siguiente):
    """Duerme hasta el siguiente turno. Si la revisión tardó más que el intervalo, SALTA los turnos perdidos
    (como time.Ticker de Go) en vez de ponerse al día de golpe."""
    siguiente += INTERVALO
    ahora = time.monotonic()
    if siguiente < ahora:
        siguiente += ((ahora - siguiente) // INTERVALO + 1) * INTERVALO
    await asyncio.sleep(siguiente - ahora)
    return siguiente


async def revisar(cliente, url):
    """None si el sitio está bien; si no, el motivo en palabras."""
    try:
        r = await cliente.get(url)
    except httpx.ConnectTimeout:
        return f"no conectó en {TIMEOUT:g} s"
    except httpx.ReadTimeout:
        return f"conectó, pero no respondió en {TIMEOUT:g} s"
    except httpx.ConnectError as e:
        return motivo_conexion(e)
    if r.status_code >= 400:
        return f"HTTP {r.status_code}"
    return None


def mensaje(nombre, caido, motivo, fallos):
    """El JSON de un webhook de Discord: content (texto) + embeds (la tarjeta)."""
    ahora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    if caido:
        return {"username": "monitor", "content": f"🔴 {nombre} CAÍDO",
                "embeds": [{"title": f"{nombre} no responde", "description": motivo, "color": ROJO,
                            "fields": [{"name": "fallos seguidos", "value": str(fallos), "inline": True},
                                       {"name": "url", "value": SITIOS[nombre], "inline": True}],
                            "timestamp": ahora}]}
    return {"username": "monitor", "content": f"🟢 {nombre} volvió",
            "embeds": [{"title": f"{nombre} responde otra vez", "color": VERDE, "timestamp": ahora}]}


async def cartero(cola, webhook, enviados):
    """Un solo envío a la vez, en orden. Si Discord contesta 429, espera lo que pide retry_after."""
    async with httpx.AsyncClient(timeout=5.0) as cliente:
        while True:
            nombre, cuerpo = await cola.get()
            for _ in range(3):
                r = await cliente.post(webhook, json=cuerpo)
                if r.status_code == 429:
                    espera = float(r.json().get("retry_after", 1))
                    print(f"{t()}  429 de Discord: espero {espera:g} s y reintento", flush=True)
                    await asyncio.sleep(espera)
                    continue
                r.raise_for_status()
                print(f"{t()}  aviso → {cuerpo['content']}: {cuerpo['embeds'][0].get('description', '')} ({r.status_code})",
                      flush=True)
                enviados[nombre] += 1
                break
            cola.task_done()


async def vigilar(nombre, url, cliente, cola, solo_cambios):
    caido, fallos = False, 0
    siguiente = time.monotonic()
    while time.monotonic() - T0 < SEGUNDOS:
        motivo = await revisar(cliente, url)
        if not solo_cambios:
            if motivo:
                await cola.put((nombre, mensaje(nombre, True, motivo, 1)))
        elif motivo:
            fallos += 1
            if fallos == UMBRAL and not caido:
                caido = True
                await cola.put((nombre, mensaje(nombre, True, f"{motivo} · {fallos} fallos seguidos", fallos)))
        else:
            if caido:
                await cola.put((nombre, mensaje(nombre, False, "", 0)))
            caido, fallos = False, 0
        siguiente = await esperar_turno(siguiente)


async def principal(modo):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        print("falta DISCORD_WEBHOOK_URL", file=sys.stderr)
        sys.exit(1)
    print(f"httpx {httpx.__version__} · cada {INTERVALO:g} s · timeout {TIMEOUT:g} s · umbral {UMBRAL} · "
          f"solo cambios: {modo == 'estados'} · {SEGUNDOS:g} s", flush=True)
    cola = asyncio.Queue()
    enviados = {n: 0 for n in SITIOS}
    tarea_cartero = asyncio.create_task(cartero(cola, webhook, enviados))
    async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
        await asyncio.gather(*(vigilar(n, u, cliente, cola, modo == "estados") for n, u in SITIOS.items()))
    await cola.join()
    tarea_cartero.cancel()
    total = sum(enviados.values())
    print(f"avisos en {SEGUNDOS:g} s: {total}  (" + " · ".join(f"{n} {c}" for n, c in enviados.items()) + ")", flush=True)


async def rondas():
    """Por rondas: gather de todos y luego dormir. La ronda dura lo que tarde el más lento."""
    cuentas = {}
    for etiqueta, timeout in (("por rondas, timeout 30 s", 30.0), ("por rondas, timeout 2 s ", TIMEOUT)):
        n, t1 = 0, time.monotonic()
        async with httpx.AsyncClient(timeout=timeout) as cliente:
            while time.monotonic() - t1 < 10:
                await asyncio.gather(*(revisar(cliente, u) for u in SITIOS.values()))
                n += 1
                await asyncio.sleep(INTERVALO)
        cuentas[etiqueta] = n
    n, t1 = 0, time.monotonic()

    async def solo_web(cliente):
        nonlocal n
        siguiente = time.monotonic()
        while time.monotonic() - t1 < 10:
            await revisar(cliente, SITIOS["web"])
            n += 1
            siguiente = await esperar_turno(siguiente)

    async def otro(cliente, url):
        while time.monotonic() - t1 < 10:
            await revisar(cliente, url)
            await asyncio.sleep(INTERVALO)

    async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
        await asyncio.gather(solo_web(cliente), *(otro(cliente, u) for k, u in SITIOS.items() if k != "web"))
    cuentas["una tarea por sitio, timeout 2 s"] = n
    for k, v in cuentas.items():
        print(f"  {k} → web revisado {v:2d} veces en 10 s")


def sin_timeout():
    print(f"timeout por defecto de httpx: {httpx.AsyncClient().timeout}")
    print(f"timeout por defecto de urllib (socket): {__import__('socket').getdefaulttimeout()}")
    for _ in range(2):
        t1 = time.monotonic()
        with urllib.request.urlopen(SITIOS["lento"]) as r:   # ⚠️ sin timeout: espera lo que haga falta
            print(f"  urlopen sin timeout → lento: {r.status} OK en {time.monotonic() - t1:.1f} s")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "estados"
    if modo == "rondas":
        asyncio.run(rondas())
    elif modo == "sin-timeout":
        sin_timeout()
    else:
        asyncio.run(principal(modo))
