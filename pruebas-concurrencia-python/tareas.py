# -*- coding: utf-8 -*-
"""Las tareas del banco. Viven en un módulo aparte para que los procesos del pool (forkserver) las puedan importar.

  cpu(semilla, n)        cálculo puro en Python: n vueltas de multiplicar, sumar y sacar el módulo.
  espera(i, ms)          E/S simulada: time.sleep(ms) y devuelve i*i.
  red(i, puerto)         E/S de verdad: abre un socket TCP al servidor local, manda i, el servidor espera y contesta i*i.
  servidor(puerto, ms)   el servidor de la prueba de red (asyncio), contesta cada línea tras esperar ms.
"""
import asyncio
import socket
import time

MOD = 1_000_003


def cpu(semilla, n):
    s = semilla
    for i in range(n):
        s = (s * 31 + i) % MOD
    return s


async def cpu_async(semilla, n):
    # Una corrutina que calcula sin un solo await: bloquea el bucle de eventos. Es justo lo que se quiere enseñar.
    return cpu(semilla, n)


def espera(i, ms):
    time.sleep(ms / 1000)
    return i * i


async def espera_async(i, ms):
    await asyncio.sleep(ms / 1000)
    return i * i


def red(i, puerto):
    with socket.create_connection(("127.0.0.1", puerto)) as s:
        s.sendall(f"{i}\n".encode())
        return int(s.makefile("r").readline())


async def red_async(i, puerto):
    r, w = await asyncio.open_connection("127.0.0.1", puerto)
    w.write(f"{i}\n".encode())
    await w.drain()
    linea = await r.readline()
    w.close()
    await w.wait_closed()
    return int(linea)


def servidor(puerto, ms):
    async def atender(r, w):
        linea = await r.readline()
        await asyncio.sleep(ms / 1000)
        w.write(f"{int(linea) ** 2}\n".encode())
        await w.drain()
        w.close()

    async def main():
        srv = await asyncio.start_server(atender, "127.0.0.1", puerto, backlog=4096)
        print("escuchando", flush=True)
        async with srv:
            await srv.serve_forever()

    asyncio.run(main())


if __name__ == "__main__":
    import sys
    servidor(int(sys.argv[1]), float(sys.argv[2]))
