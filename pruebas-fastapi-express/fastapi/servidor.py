# El servidor de la revancha, lado Python: FastAPI + uvicorn.
# Mismo contrato que el 152: /suma hace CPU de verdad, /espera simula E/S.
import asyncio
import sys
import time

from fastapi import FastAPI

ARRANQUE = time.perf_counter()
app = FastAPI()


@app.get("/suma")
def suma(n: int = 0):
    t0 = time.perf_counter_ns()
    s = 0
    for i in range(1, n + 1):
        s += i * i % 1000003
    ns = time.perf_counter_ns() - t0
    return {"lang": "fastapi", "n": n, "suma": s, "ns": ns}


@app.get("/espera")
async def espera(ms: int = 0):
    await asyncio.sleep(ms / 1000)
    return {"lang": "fastapi", "n": ms, "suma": 0, "ns": 0}


@app.on_event("startup")
async def listo():
    print(f"LISTO_EN_MS {(time.perf_counter() - ARRANQUE) * 1000:.3f}",
          file=sys.stderr, flush=True)
