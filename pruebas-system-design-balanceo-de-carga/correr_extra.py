# -*- coding: utf-8 -*-
"""Segunda parte del banco del vídeo 345 (balanceo de carga). Escribe SALIDA-extra.md.

Aparte de correr.py para no rehacer sus números (que ya están en el guion). Reutiliza su laboratorio:
  5  round robin con pesos (5, 5, 1)          6  random(2): dos al azar, la más libre
  7  sin chequeos pero con option redispatch  8  hash por IP con 20 clientes de IP distinta
  9  nginx y un POST durante la caída (no idempotente: ¿lo reintenta?)

    python correr_extra.py
"""
import re
import threading
import time
import datetime

import correr as C

C.salida = []
p = C.p


def bloque(titulo, salida):
    p(titulo)
    for l in salida.splitlines():
        p(l)


def main():
    C.limpiar()
    C.docker("network", "create", "--subnet", C.SUBRED, C.RED, check=True)
    C.compilar_carga()
    url = f"http://{C.LB_IP}/"
    try:
        C.replicas()
        C.salida.append("```")
        p("== 5 · Round robin con pesos: r1 y r2 pesan 5, r3 pesa 1 ==")
        C.haproxy("roundrobin", pesos={"r1": 5, "r2": 5, "r3": 1})
        bloque("$ HAProxy · balance roundrobin · weight 5/5/1", C.carga("-url", url, "-n", "3000", "-c", "30"))

        p("")
        p("== 6 · random(2): dos réplicas al azar, y la que tenga menos conexiones ==")
        C.haproxy("random(2)")
        bloque("$ HAProxy · balance random(2)", C.carga("-url", url, "-n", "3000", "-c", "30"))

        p("")
        p("== 7 · Sin chequeos, pero con option redispatch ==")
        C.haproxy("roundrobin", extra="  option redispatch\n  retries 3")
        C.caida("HAProxy sin chequeos + option redispatch")

        p("")
        p("== 8 · Hash por IP con 20 clientes, cada uno con su IP (30 peticiones cada uno) ==")
        C.haproxy("source")
        total = {}
        # Cada contenedor con su IP fija: lanzados uno tras otro, Docker les daba a todos la misma
        # IP libre (medido: las 600 a r3, que eran 20 veces el mismo cliente).
        for i in range(20):
            o = C.docker("run", "--rm", "--network", C.RED, "--ip", f"10.77.21.{100 + i}",
                         "-v", f"{(C.AQUI / 'carga').as_posix()}:/w:ro", "alpine:3.22",
                         "/w/carga", "-url", url, "-n", "30", "-c", "1")
            for rep, n in re.findall(r"(r\d) (\d+)", o.split("reparto:")[-1]):
                total[rep] = total.get(rep, 0) + int(n)
        p("$ 20 × carga -n 30 -c 1   (20 contenedores, de 10.77.21.100 a 10.77.21.119)")
        p("  reparto: " + " · ".join(f"{k} {total.get(k, 0)}" for k in ("r1", "r2", "r3")))

        p("")
        p("== 9 · nginx y un POST durante la caída ==")
        C.nginx()
        p("$ carga -post -durante 12s   (nginx pasivo; a los 3 s muere el proceso de r2)")
        o = C.carga("-url", url, "-c", "10", "-durante", "12s", "-post",
                    "-morir-a", "3s", "-morir-url", f"http://{C.REPLICAS['r2'][0]}:8000/morir")
        for l in o.splitlines():
            p(l)
        C.salida.append("```")
    finally:
        C.limpiar()
    cab = ["# SALIDA — balanceo de carga, segunda parte (cultura-devops, vídeo 345)", "",
           "> Generado por `correr_extra.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}` · mismo laboratorio que SALIDA.md"]
    (C.AQUI / "SALIDA-extra.md").write_bytes(("\n".join(cab) + "\n\n" + "\n".join(C.salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA-extra.md")


if __name__ == "__main__":
    main()
