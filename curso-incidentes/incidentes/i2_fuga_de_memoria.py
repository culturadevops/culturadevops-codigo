# -*- coding: utf-8 -*-
"""Incidente 2 · Una fuga de memoria que tarda días (aquí, un minuto y pico).

Una caché «para acelerar» guarda cada pedido y no borra nunca nada. En producción tarda días en
llenar la memoria; aquí, con 200 KB por pedido, un minuto y pico. El síntoma no es «memoria»: es
que la tienda se reinicia sola de vez en cuando, y cada reinicio corta lo que estaba a medias.
La alerta buena no espera a que se acabe: predice cuándo se va a acabar.
"""
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

from comun import AQUI, PROM, TIENDA, Cronologia, Trafico, docker, esperar_alerta, esperar_tienda, postmortem, titulo

MiB = 1024 * 1024


def desplegar(**entorno):
    subprocess.run(["docker", "compose", "up", "-d", "--force-recreate", "tienda"], cwd=AQUI,
                   env=dict(os.environ, MSYS_NO_PATHCONV="1", **entorno), capture_output=True, check=True)
    esperar_tienda()


def memoria(desde, paso=5):
    fin = time.time()
    q = urllib.parse.urlencode({"query": "tienda_memoria_bytes", "start": desde, "end": fin, "step": paso})
    d = json.loads(urllib.request.urlopen(f"{PROM}/api/v1/query_range?{q}").read())
    vals = d["data"]["result"][0]["values"] if d["data"]["result"] else []
    return [int(float(v) / MiB) for _, v in vals]


def eventos(desde, cid):
    """Lo que Docker apuntó de ese contenedor: el oom del núcleo y la muerte con su código."""
    r = subprocess.run(["docker", "events", "--since", str(int(desde)), "--until", str(int(time.time())),
                        "--filter", f"container={cid}", "--filter", "event=oom", "--filter", "event=die",
                        "--format", "{{.Action}} {{index .Actor.Attributes \"exitCode\"}}"],
                       capture_output=True, text=True)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]


def reinicios(cid):
    return int(subprocess.run(["docker", "inspect", "-f", "{{.RestartCount}}", cid],
                              capture_output=True, text=True).stdout.strip() or 0)


cron = Cronologia()
inicio = time.time()
titulo("2.1 · Se despliega la versión con la caché")
desplegar(FUGA="1")
cid = docker("ps", "-q", "tienda").strip()
t_despliegue = time.time()
cron.marca("desplegada la versión con caché (FUGA=1) · límite del contenedor: 160 MiB, sin swap")

with Trafico(f"{TIENDA}/pedido", hilos=2, pausa=0.2) as tr:
    titulo("2.2 · La alerta predictiva: antes de que se acabe")
    t = esperar_alerta("MemoriaSeAgota", inicio)
    cron.marca("ALERTA MemoriaSeAgota: «al ritmo actual, se acaba en menos de 2 minutos»", t)
    print(f"  memoria en ese momento: {memoria(time.time() - 5)[-1]} MiB de 160")

    titulo("2.3 · Nadie hace caso, y el núcleo la mata")
    for _ in range(600):
        if reinicios(cid) > 0:
            break
        time.sleep(0.2)
    cron.marca(f"la tienda muere y Docker la levanta (reinicios: {reinicios(cid)})")
    time.sleep(3)
    for e in eventos(t_despliegue, cid):
        print(f"  docker events: {e}")
    print(f"  tráfico hasta aquí: {tr.resumen()}")

    titulo("2.4 · El diente de sierra: la memoria cada 5 s, en MiB")
    time.sleep(25)
    print("  " + " ".join(str(x) for x in memoria(t_despliegue)))

titulo("2.5 · Mitigar: la caché con un tope de 100 entradas")
desplegar(FUGA="1", CACHE_MAX="100")
cid = docker("ps", "-q", "tienda").strip()
t_arreglo = time.time()
cron.marca("MITIGADO: desplegada la caché con tope (CACHE_MAX=100)")
with Trafico(f"{TIENDA}/pedido", hilos=2, pausa=0.2) as tr:
    time.sleep(90)
    print("  memoria cada 5 s: " + " ".join(str(x) for x in memoria(t_arreglo)) + " MiB")
    print(f"  tráfico: {tr.resumen()} · reinicios: {reinicios(cid)}")
cron.marca("90 s con el mismo tráfico: la memoria se queda plana y no hay reinicios")

titulo("2.6 · El postmortem")
postmortem(2, "Una fuga de memoria que tarda días", cron,
           resumen="La tienda se reinició sola por falta de memoria. Una caché nueva guardaba cada "
                   "pedido sin borrar ninguno.",
           causa="La caché no tenía límite. Cada pedido añadía 200 KB y nunca se liberaban. Al llegar al "
                 "límite del contenedor, el núcleo mató el proceso (evento oom, código 137) y Docker lo "
                 "levantó otra vez, cortando las peticiones que tenía a medias.",
           bien=["La alerta predictiva avisó ANTES del reinicio, con tiempo para actuar.",
                 "docker events guarda el oom y el código 137: la causa no hay que adivinarla."],
           mal=["La alerta predictiva no despertó a nadie: se trató como un aviso más.",
                "docker inspect, después del reinicio, ya enseña el proceso nuevo: hay que mirar los eventos.",
                "Una caché sin tope pasó la revisión de código."],
           acciones=["Toda caché lleva tope de entradas o de memoria, y una métrica de su tamaño.",
                     "La alerta MemoriaSeAgota es de las que despiertan.",
                     "Prueba de carga larga antes de desplegar cambios de caché."])
