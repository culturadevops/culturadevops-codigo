# -*- coding: utf-8 -*-
"""Incidente 3 · El certificado que caducó un domingo.

Un certificado de 90 días que alguien renovaba a mano. La renovación automática no estaba
configurada para ese dominio. Caduca un domingo: nadie mira, los clientes no pueden pagar.
La alerta que lo habría evitado no mira si la web funciona: mira cuántos días le quedan.
Aquí se comprime: un certificado con 3 días de vida, y «el domingo» llega con un cambio de fichero.
"""
import json
import subprocess
import time
import urllib.request

from comun import AQUI, Cronologia, docker, esperar_alerta, postmortem, prom1, titulo

IMG = "python:3.13-slim"     # trae openssl 3.5
VOL = "curso-incidentes_certs"


def openssl(script):
    r = subprocess.run(["docker", "run", "--rm", "-v", f"{VOL}:/c", "-w", "/c", IMG, "sh", "-c", script],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-500:])
    return r.stdout


def poner(cert):
    openssl(f"cp {cert}.pem actual.pem && cp {cert}.key actual.key")
    docker("exec", "-T", "web-tls", "nginx", "-s", "reload")


def dias():
    v = prom1('(probe_ssl_earliest_cert_expiry{job="certificado"} - time()) / 86400')
    return f"{v:.1f}" if v is not None else "-"


def sonda():
    """Lo que ve la sonda HTTPS (blackbox) ahora mismo, con su motivo si falla."""
    salida = docker("exec", "-T", "blackbox", "wget", "-qO-",
                    "http://127.0.0.1:9115/probe?module=https&target=https://api.tienda.test&debug=true", check=False)
    ok = next((l for l in salida.splitlines() if l.startswith("probe_success ")), "probe_success ?")
    err = next((l.split("msg=")[-1].strip('"') for l in salida.splitlines() if "level=error" in l or "level=ERROR" in l), "")
    return ok + (f"  · {err}" if err else "")


openssl("""
set -e
q() { "$@" >/dev/null 2>&1; }
q openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout raiz.key -out raiz.pem -days 3650 -subj "/CN=CA del curso" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"
printf "subjectAltName=DNS:api.tienda.test\\n" > san.ext
hoja() { q openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout $1.key -out $1.csr -subj "/CN=api.tienda.test"
         q openssl x509 -req -in $1.csr -CA raiz.pem -CAkey raiz.key -CAcreateserial -out $1.pem -extfile san.ext $2; }
hoja tres-dias "-days 3"
hoja caducado "-not_before $(date -u -d '-90 days' +%Y%m%d%H%M%SZ) -not_after $(date -u -d '-1 hour' +%Y%m%d%H%M%SZ)"
hoja renovado "-days 90"
cp tres-dias.pem actual.pem && cp tres-dias.key actual.key
chmod 644 *.key
""")
docker("--profile", "certificado", "up", "-d", "blackbox", "web-tls")
time.sleep(3)

cron = Cronologia()
inicio = time.time()
titulo("3.1 · La web funciona. Y le quedan 3 días")
time.sleep(12)
print(f"  sonda: {sonda()}")
print(f"  PromQL: días que le quedan = {dias()}")
t = esperar_alerta("CertificadoCaducaPronto", inicio)
cron.marca("ALERTA CertificadoCaducaPronto: «caduca en menos de 14 días» (y nadie la atiende)", t)

titulo("3.2 · Llega el domingo")
poner("caducado")
cron.marca("el certificado caduca")
cliente = subprocess.run(["docker", "run", "--rm", "--network", "curso-incidentes_default", "-v", f"{VOL}:/c:ro", IMG,
                          "python", "-c",
                          "import ssl,urllib.request as u\n"
                          "c=ssl.create_default_context(cafile='/c/raiz.pem')\n"
                          "try: print(u.urlopen('https://api.tienda.test',context=c,timeout=5).status)\n"
                          "except Exception as e: print(getattr(e,'reason',e))"],
                         capture_output=True, text=True)
print(f"  un cliente: {cliente.stdout.strip()}")
t = esperar_alerta("CertificadoFalla", inicio)
cron.marca("ALERTA CertificadoFalla: «la comprobación HTTPS falla»", t)

titulo("3.3 · Diagnóstico")
print(f"  sonda: {sonda()}")
fin = openssl("openssl x509 -in actual.pem -noout -enddate").strip()
print(f"  openssl x509 -enddate: {fin}")
cron.marca("diagnóstico: el certificado servido está caducado")

titulo("3.4 · Mitigar: el certificado renovado")
poner("renovado")
cron.marca("MITIGADO: certificado renovado (90 días) y nginx recargado")
time.sleep(12)
print(f"  sonda: {sonda()}")
print(f"  PromQL: días que le quedan = {dias()}")
t = esperar_alerta("CertificadoFalla", inicio, estado="resolved")
cron.marca("la alerta CertificadoFalla se resuelve", t)
docker("--profile", "certificado", "stop", "blackbox", "web-tls")

titulo("3.5 · El postmortem")
postmortem(3, "El certificado que caducó un domingo", cron, desde="el certificado caduca",
           resumen="La web dejó de aceptar conexiones seguras: el certificado caducó. La alerta de "
                   "«caduca pronto» había saltado antes, y no la atendió nadie.",
           causa="El dominio se renovaba a mano y la renovación automática no lo cubría. La alerta de "
                 "caducidad existía, pero era un aviso más en un canal que nadie mira el fin de semana.",
           bien=["La sonda HTTPS detectó el fallo sola, con el motivo exacto.",
                 "La alerta de días restantes saltó con margen."],
           mal=["La alerta con margen no tenía dueño ni urgencia.",
                "Un certificado renovado a mano es un certificado que caduca."],
           acciones=["Renovación automática para TODOS los dominios, y una prueba de que funciona.",
                     "La alerta de caducidad abre una tarea con responsable, no solo un aviso.",
                     "Inventario de certificados con su fecha de caducidad."])
