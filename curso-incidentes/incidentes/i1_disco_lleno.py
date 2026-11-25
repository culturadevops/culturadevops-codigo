# -*- coding: utf-8 -*-
"""Incidente 1 · Se llenó el disco, y lo que falló fue otra cosa.

La alerta dice «errores». No dice «disco». Alguien activó el modo depuración para investigar
otra cosa y se fue a casa: cada línea de auditoría pasa de unos 70 bytes a más de 50 KB, llena su
disco, y cada pedido que no se puede auditar falla con un 500.
"""
import time
import urllib.request

from comun import TIENDA, Cronologia, Trafico, busca, docker, esperar_alerta, loki, postmortem, prom, titulo

cron = Cronologia()
inicio = time.time()
titulo("1.1 · Un martes normal")
with Trafico(f"{TIENDA}/pedido", hilos=3, pausa=0.2) as tr:
    time.sleep(8)
    cron.marca(f"tráfico normal · {tr.resumen()}")
    req = urllib.request.Request(f"{TIENDA}/admin/depuracion", method="POST", headers={"X-Usuario": "ana"})
    urllib.request.urlopen(req).read()
    cron.marca("alguien activa el modo depuración (y se olvida)")

    titulo("1.2 · Salta la alerta")
    t = esperar_alerta("ErroresAltos", inicio)
    cron.marca("ALERTA ErroresAltos: «Más del 5% de las peticiones fallan»", t)
    print(f"  tráfico desde el principio: {tr.resumen()}")

    titulo("1.3 · Diagnóstico: ¿qué falla?")
    for m, v in prom('sum by (ruta, codigo) (rate(tienda_peticiones_total[30s]))'):
        print(f"  PromQL  {m['ruta']:8s} {m['codigo']}: {v:5.2f} por segundo")
    cron.marca("las métricas: solo falla /pedido, con 500")

    titulo("1.4 · Diagnóstico: ¿por qué? Los registros")
    for h, l in loki('{app="tienda", nivel="error"}', inicio, limite=2):
        print(f"  LogQL   {time.strftime('%H:%M:%SZ', time.gmtime(h))}  {l}")
    cron.marca("los registros: «No space left on device»")

    titulo("1.5 · ¿Qué llenó el disco? Y el cambio reciente")
    print("  " + docker("exec", "-T", "tienda", "df", "-h", "/datos").splitlines()[-1])
    print("  " + docker("exec", "-T", "tienda", "ls", "-la", "/datos").splitlines()[-1])
    for h, l in loki('{app="tienda"} |= "depuracion"', inicio, limite=1):
        print(f"  LogQL   {time.strftime('%H:%M:%SZ', time.gmtime(h))}  {l}")
    cron.marca("causa: el modo depuración, activado hace unos minutos")

    titulo("1.6 · Mitigar: apagar la depuración y vaciar el fichero")
    docker("restart", "tienda")                      # la depuración no sobrevive a un reinicio
    docker("exec", "-T", "tienda", "sh", "-c", ": > /datos/auditoria.log")
    cron.marca("MITIGADO: tienda reiniciada (depuración apagada) y auditoría vaciada")
    print("  " + docker("exec", "-T", "tienda", "df", "-h", "/datos").splitlines()[-1])
    t = esperar_alerta("ErroresAltos", inicio, estado="resolved")
    cron.marca("la alerta se resuelve sola", t)
    print(f"  tráfico total del incidente: {tr.resumen()}")

titulo("1.7 · El postmortem")
postmortem(1, "Se llenó el disco, y lo que falló fue otra cosa", cron,
           resumen="Una parte de los pedidos falló con 500. El disco de la auditoría se llenó porque "
                   "el modo depuración hizo que cada línea pasara de unos 70 bytes a más de 50 KB.",
           causa="El modo depuración se activó a mano para otra investigación y nadie lo apagó. La "
                 "auditoría es obligatoria: si no se escribe, el pedido falla. Un disco de auditoría sin "
                 "alerta de espacio convirtió un olvido en errores para los clientes.",
           bien=["La alerta de errores saltó sola, sin que llamara un cliente.",
                 "Los registros decían la causa exacta: «No space left on device»."],
           mal=["La alerta dice el síntoma (errores), no la causa (disco).",
                "El modo depuración no caduca: se queda encendido hasta que alguien se acuerda."],
           acciones=["Alerta de espacio en el disco de auditoría, al 80%.",
                     "El modo depuración se apaga solo a los 30 minutos.",
                     "Rotación y límite de tamaño para el fichero de auditoría."])
