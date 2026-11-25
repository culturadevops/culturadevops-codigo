#!/usr/bin/env python3
"""flota.py — el mismo comando en muchos servidores por SSH, con asyncssh (vídeo 800 de cultura-devops).

    flota.py -hosts hosts-50.txt [-p 50] [-cmd revisar] [-conectar 3] [-timeout 10] [-llegada] [-ingenuo] [-inseguro] [-json]

Código de salida: 0 todo bien · 1 algún host dio código distinto de 0 · 2 algún host no respondió.
-ingenuo: sin connect_timeout ni timeout del comando (la trampa). -inseguro: known_hosts=None (no comprueba la huella).
"""
import argparse
import asyncio
import json
import sys
import time

import asyncssh


async def uno(host, a, sem):
    async with sem:
        t0 = time.monotonic()
        opciones = dict(username=a.usuario, client_keys=[a.clave], known_hosts=None if a.inseguro else a.known)
        if not a.ingenuo:
            opciones["connect_timeout"] = a.conectar
        try:
            async with asyncssh.connect(host, **opciones) as con:
                r = await con.run(a.cmd, timeout=None if a.ingenuo else a.timeout)
            return dict(host=host, rc=r.exit_status, s=time.monotonic() - t0, out=r.stdout.strip(), err=r.stderr.strip())
        except asyncssh.TimeoutError:
            return dict(host=host, rc=None, s=time.monotonic() - t0, error=f"el comando no terminó en {a.timeout:g}s")
        except asyncio.TimeoutError:                 # connect_timeout: ni TCP ni el saludo SSH en ese tiempo
            return dict(host=host, rc=None, s=time.monotonic() - t0, error=f"no conectó en {a.conectar:g}s")
        except (OSError, asyncssh.Error) as e:
            return dict(host=host, rc=None, s=time.monotonic() - t0, error=f"{type(e).__name__}: {e}".rstrip(": "))


def linea(r):
    if r["rc"] is None:
        return f"{r['host']:<6} ERR  {r['s']:5.1f}s  {r['error']}"
    t = f"{r['host']:<6} {r['rc']:>3}  {r['s']:5.1f}s  {r['out']}"
    if r["err"]:
        t += f"\n{r['host']:<6} stderr        {r['err']}"
    return t


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-hosts", required=True)
    ap.add_argument("-p", type=int, default=10, help="cuántos a la vez")
    ap.add_argument("-cmd", default="revisar")
    ap.add_argument("-usuario", default="admin")
    ap.add_argument("-clave", default="/root/.ssh/id_ed25519")
    ap.add_argument("-known", default="/root/.ssh/known_hosts")
    ap.add_argument("-conectar", type=float, default=3)
    ap.add_argument("-timeout", type=float, default=10)
    ap.add_argument("-llegada", action="store_true", help="imprime cada uno al terminar")
    ap.add_argument("-ingenuo", action="store_true")
    ap.add_argument("-inseguro", action="store_true")
    ap.add_argument("-json", action="store_true")
    a = ap.parse_args()

    hosts = [h.strip() for h in open(a.hosts) if h.strip()]
    sem = asyncio.Semaphore(a.p)
    t0 = time.monotonic()
    tareas = [asyncio.create_task(uno(h, a, sem)) for h in hosts]
    if a.llegada:
        res = []
        for t in asyncio.as_completed(tareas):
            r = await t
            res.append(r)
            print(linea(r), flush=True)
    else:
        res = await asyncio.gather(*tareas)          # mismo orden que la lista de hosts
        if a.json:
            print(json.dumps(res, ensure_ascii=False))
        else:
            for r in res:
                print(linea(r))
    ok = sum(r["rc"] == 0 for r in res)
    malos = sum(r["rc"] not in (0, None) for r in res)
    caidos = sum(r["rc"] is None for r in res)
    if not a.json:
        print(f"{len(res)} hosts · {ok} ok · {malos} con código distinto de 0 · {caidos} sin respuesta · "
              f"{time.monotonic() - t0:.1f}s en total")
    return 2 if caidos else 1 if malos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
