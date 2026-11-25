# -*- coding: utf-8 -*-
"""Incidente 4 · El despliegue que perdió peticiones a medias.

Dos réplicas detrás de un balanceador, y un despliegue «por turnos»: primero una, luego la otra.
Parece que no se cae nada. Pero cada réplica que se para corta lo que tenía a medias, y el
balanceador le sigue mandando peticiones hasta que se entera. Los pagos de esos segundos fallan.

Y una sorpresa de Docker: Python en un contenedor es el PID 1, y el núcleo no aplica la acción por
defecto de SIGTERM al PID 1. El proceso lo IGNORA: `docker stop` espera 10 segundos y lo mata con
SIGKILL. Se mide abajo.
"""
import os
import subprocess
import time
import urllib.request

from comun import AQUI, Cronologia, Trafico, postmortem, titulo

LB = "http://127.0.0.1:18080"


def compose(*args, **entorno):
    r = subprocess.run(["docker", "compose", "--profile", "despliegue", *args], cwd=AQUI, capture_output=True,
                       text=True, env=dict(os.environ, MSYS_NO_PATHCONV="1", **entorno))
    if r.returncode != 0:
        raise SystemExit(r.stderr[-400:])
    return r.stdout


def lista(svc):
    for _ in range(120):
        r = subprocess.run(["docker", "compose", "--profile", "despliegue", "exec", "-T", svc, "python", "-c",
                            "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/salud', timeout=1)"],
                           cwd=AQUI, capture_output=True, env=dict(os.environ, MSYS_NO_PATHCONV="1"))
        if r.returncode == 0:
            return
        time.sleep(0.25)


def en_rotacion(svc, limite=15):
    """¿El balanceador ya le manda tráfico a la réplica NUEVA? Se pregunta al balanceador, no a ella:
    la réplica puede estar lista y el balanceador seguir apuntando a la IP de la vieja."""
    cid = compose("ps", "-q", svc).strip()
    ip = subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", cid],
                        capture_output=True, text=True).stdout.strip()
    fin = time.time() + limite
    while time.time() < fin:
        try:
            with urllib.request.urlopen(f"{LB}/salud", timeout=2) as r:
                if ip and ip in (r.headers.get("X-Replica") or ""):
                    return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def desplegar_por_turnos(cron, **entorno):
    for svc in ("tienda-a", "tienda-b"):
        t0 = time.time()
        compose("up", "-d", "--force-recreate", "--no-deps", svc, **entorno)
        para = time.time() - t0
        lista(svc)
        visto = en_rotacion(svc)
        cron.marca(f"{svc}: parada y recreada en {para:.1f} s · el balanceador "
                   + ("ya le manda tráfico" if visto else "NO la ve en 15 s"))


def parar_y_medir(svc):
    """docker stop, cronometrado, y el código con el que murió el proceso (137 = SIGKILL)."""
    cid = compose("ps", "-q", svc).strip()
    t0 = time.time()
    subprocess.run(["docker", "stop", cid], capture_output=True)
    dura = time.time() - t0
    codigo = subprocess.run(["docker", "inspect", "-f", "{{.State.ExitCode}}", cid], capture_output=True,
                            text=True).stdout.strip()
    return f"docker stop {svc}: {dura:.1f} s · código de salida {codigo}"


def escenario(nombre, entorno):
    compose("up", "-d", "--force-recreate", "tienda-a", "tienda-b", "balanceador", **entorno)
    lista("tienda-a")
    lista("tienda-b")
    time.sleep(2)
    cron = Cronologia()
    with Trafico(f"{LB}/lento", hilos=8, pausa=0.05, timeout=15) as tr:
        time.sleep(4)
        cron.marca(f"tráfico de pagos (1 s cada uno) · {tr.resumen()}")
        desplegar_por_turnos(cron, **entorno)
        time.sleep(4)
    cron.marca(f"despliegue terminado · {tr.resumen()}")
    return cron, tr


titulo("4.1 · Un despliegue por turnos, como en los tutoriales")
cron1, tr1 = escenario("ingenuo", {"APAGADO": "", "BALANCEADOR": "ingenuo"})
malos = sum(v for k, v in tr1.res.items() if k != "200")
print(f"  pagos fallidos durante el despliegue: {malos}")

titulo("4.2 · ¿Por qué tarda tanto en pararse? Lo que hace docker stop")
print("  " + parar_y_medir("tienda-a"))

titulo("4.3 · Lo correcto: atender SIGTERM, terminar lo que hay a medias, y un balanceador que reintenta")
cron2, tr2 = escenario("bueno", {"APAGADO": "bueno", "BALANCEADOR": "bueno"})
malos2 = sum(v for k, v in tr2.res.items() if k != "200")
print(f"  pagos fallidos durante el despliegue: {malos2}")
cron2.marca("MITIGADO: apagado limpio + reintento en el balanceador")
print("  " + parar_y_medir("tienda-a"))
compose("stop", "tienda-a", "tienda-b", "balanceador")

titulo("4.4 · El postmortem")
cron1.eventos += [(s + cron1.eventos[-1][0], t) for s, t in cron2.eventos]
postmortem(4, "El despliegue que perdió peticiones a medias", cron1,
           resumen=f"Un despliegue por turnos de dos réplicas hizo fallar {malos} pagos. Nadie vio una caída: "
                   "solo errores sueltos durante unos segundos.",
           causa="La aplicación no atendía SIGTERM. Como PID 1 del contenedor, la señal se ignora: Docker "
                 "esperaba 10 s y la mataba con SIGKILL, cortando los pagos a medias. El balanceador no "
                 "reintentaba en la otra réplica.",
           bien=["Desplegar de una réplica en una réplica: nunca se quedó sin ninguna.",
                 f"Con el apagado limpio y el reintento, el mismo despliegue: {malos2} pagos fallidos."],
           mal=["Nadie medía errores DURANTE el despliegue: el panel solo enseñaba el antes y el después.",
                "Los 10 segundos de docker stop parecían «lo normal»."],
           acciones=["Toda aplicación atiende SIGTERM: deja de aceptar y termina lo que tiene a medias.",
                     "El balanceador reintenta en otra réplica si una no contesta.",
                     "El despliegue se valida con tráfico de prueba y cuenta los errores mientras dura."])
