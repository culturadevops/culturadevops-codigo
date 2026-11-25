# -*- coding: utf-8 -*-
"""pruebas_wazuh_03.py — mide de verdad lo que enseña la lección 3 del curso de Wazuh (vídeo 63).

Enrola el agente DE CERO contra el laboratorio vivo y guarda la salida literal en
`recursos/pruebas-wazuh-03/SALIDA.md`. Ninguna cifra del vídeo puede venir de otro sitio.

⛔ Los tres fallos que enseña la lección NO se fingen: se provocan de verdad.
   1. Instalar el agente sin fijar la versión → el manager lo rechaza.
   2. Y arreglarlo NO es reinstalar: `dpkg` se queda parado en una pregunta y el paquete
      queda a medio configurar, con `ossec.conf` sin tocar.
   3. Provocar un evento en un Ubuntu pelado → no llega nada, porque no hay `auth.log`.

⚠️ EMPIEZA RECREANDO LA VÍCTIMA. Es la única forma de que la medición sea la de un montaje
desde cero, y no la de un contenedor que ya arrastra intentos anteriores.

    python canales/cultura-devops/investigacion/pruebas_wazuh_03.py
"""
import io
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(r"<repo>\pruebas-wazuh-03")
LAB = Path(r"<proyecto>\canales\cultura-devops\pendientes\_lab-wazuh")


def dentro(cont, guion, t=1200):
    """Ejecuta un guion de shell DENTRO de un contenedor, por stdin.

    ⛔ En BINARIO a propósito. Con `text=True`, Python traduce los saltos de línea al estilo de
    Windows; el shell del contenedor recibe `set -e` con un retorno de carro pegado y contesta
    `sh: 1: set: Illegal option -`. Las trece pruebas fallaron así en la primera corrida
    (2026-08-24), y el mensaje no se parecía en nada a su causa."""
    p = subprocess.run(["docker", "exec", "-i", cont, "sh"], input=guion.encode("utf-8"),
                       capture_output=True, timeout=t)
    return (p.stdout + p.stderr).decode("utf-8", "replace").replace("\r\n", "\n").rstrip()


def mgr(orden):
    return dentro("lab-wazuh-manager", orden, t=300)


def vic(orden, t=1200):
    return dentro("lab-wazuh-victima", orden, t)


def agentes():
    return mgr("/var/ossec/bin/agent_control -l")


def victima_activa():
    """⛔ Mirar solo si «Active» aparece en la salida NO vale: el propio manager sale como
    `Active/Local` y la condición se cumple siempre. En la primera corrida eso dio un falso
    «activo en 0,2 s» con el agente en `Never connected`. Hay que mirar SU línea."""
    for l in agentes().splitlines():
        if "Name: victima" in l:
            return "Active" in l and "Never connected" not in l
    return False


def alertas():
    s = mgr("wc -l < /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 0")
    m = re.findall(r"\d+", s)
    return int(m[-1]) if m else 0


BLOQUES = []
FALLOS = []


def anota(titulo, pregunta, orden, salida, nota=None):
    if not salida.strip():
        FALLOS.append(titulo)
    BLOQUES.append(dict(titulo=titulo, pregunta=pregunta, orden=orden, salida=salida, nota=nota))
    print(f"  · {titulo}")


# ══ 0 · víctima nueva ══════════════════════════════════════════════════════════════════
def paso0():
    print("  · recreando la víctima (montaje desde cero)")
    subprocess.run(["docker", "compose", "rm", "-sf", "victima"], cwd=LAB,
                   capture_output=True, timeout=300)
    subprocess.run(["docker", "compose", "up", "-d", "victima"], cwd=LAB,
                   capture_output=True, timeout=300)
    time.sleep(3)
    # Los registros viejos del manager estorban: si no, el agente nuevo coge otro id y la lista
    # sale con fantasmas. Se borran los registros, no el manager.
    for i in ("001", "002", "003"):
        mgr(f"/var/ossec/bin/manage_agents -r {i} >/dev/null 2>&1; true")


# ══ 1 · el punto de partida ════════════════════════════════════════════════════════════
def paso1():
    anota("1 · De qué partimos: un Ubuntu pelado",
          "¿Qué hay en la máquina que vamos a vigilar, antes de tocar nada?",
          "docker exec lab-wazuh-victima sh -c '...'",
          vic("grep PRETTY /etc/os-release; echo '---'; "
              "ls -la /var/log/auth.log 2>&1; echo '---'; ls /var/ossec/bin 2>&1 | head -2"),
          nota="Ni agente ni `auth.log`. Un `ubuntu:24.04` no trae syslog: el fichero que todo "
               "el mundo da por hecho **no existe**.")
    anota("2 · Y qué ve el manager", "¿Cuántos agentes hay ahora mismo?",
          "docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l", agentes())


# ══ 2 · repositorio y fallo de versión ═════════════════════════════════════════════════
REPO = """export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl gpg lsb-release apt-transport-https ca-certificates >/dev/null 2>&1
curl -sS https://packages.wazuh.com/key/GPG-KEY-WAZUH \
  | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import 2>/dev/null
chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
  > /etc/apt/sources.list.d/wazuh.list
apt-get update -qq
apt-cache policy wazuh-agent | sed -n '2,3p'
"""

SIN_FIJAR = """export DEBIAN_FRONTEND=noninteractive
WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \
  apt-get install -y -qq wazuh-agent >/dev/null 2>&1
/var/ossec/bin/wazuh-control start >/dev/null 2>&1 || true
sleep 15
grep -iE "must be lower|Unable to add" /var/ossec/logs/ossec.log | tail -4
"""


def paso2():
    anota("3 · El repositorio y la versión que ofrece",
          "Si escribes `apt install wazuh-agent`, ¿qué versión te instala?",
          "apt-cache policy wazuh-agent", vic(REPO),
          nota="El repositorio siempre ofrece la ÚLTIMA. El manager de este laboratorio es la "
               "4.9.2.")
    anota("4 · ⛔ Sin fijar la versión, el manager lo rechaza",
          "¿Qué pasa si instalas el agente sin decir qué versión quieres?",
          "apt-get install -y wazuh-agent      # sin versión\n"
          "/var/ossec/bin/wazuh-control start\n"
          "grep ERROR /var/ossec/logs/ossec.log", vic(SIN_FIJAR),
          nota="Límite duro de Wazuh: **el agente nunca puede ser más nuevo que el manager**. Y "
               "el mensaje no sale en la pantalla del `apt`: hay que ir al registro del agente.")
    anota("5 · Y en el manager, nada", "¿Se enroló de todas formas?",
          "docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l", agentes())


# ══ 3 · el arreglo que no arregla ══════════════════════════════════════════════════════
REINSTALAR = """export DEBIAN_FRONTEND=noninteractive
WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \
  apt-get install -y -qq --allow-downgrades wazuh-agent=4.9.2-1 2>&1 | tail -5
echo "--- estado del paquete ---"
dpkg -l wazuh-agent | tail -1 | cut -c1-42
echo "--- a quien apunta ossec.conf ---"
grep -A1 '<server>' /var/ossec/etc/ossec.conf | head -2
"""


def paso3():
    anota("6 · ⛔ Y arreglarlo no es simplemente reinstalar",
          "Fijo la versión encima de la instalación mala. ¿Ya está?",
          "apt-get install -y --allow-downgrades wazuh-agent=4.9.2-1", vic(REINSTALAR),
          nota="`dpkg` se para en una pregunta sobre el fichero de servicio que dejó la versión "
               "nueva, no hay nadie para contestarla, y el paquete se queda en **`iU`**: "
               "desempaquetado y SIN configurar. Y quien lee `WAZUH_MANAGER` y escribe "
               "`ossec.conf` es justo el paso de configuración que no llegó a correr. Por eso "
               "sigue poniendo `MANAGER_IP`.")


# ══ 4 · la instalación limpia ══════════════════════════════════════════════════════════
LIMPIA = """export DEBIAN_FRONTEND=noninteractive
dpkg --remove --force-remove-reinstreq wazuh-agent >/dev/null 2>&1 || true
apt-get purge -y -qq wazuh-agent >/dev/null 2>&1 || true
rm -rf /var/ossec /etc/systemd/system/wazuh-agent.service
echo "paquetes wazuh tras la purga: $(dpkg -l | grep -c wazuh-agent)"
WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \
  apt-get install -y -qq -o Dpkg::Options::=--force-confnew wazuh-agent=4.9.2-1 2>&1 | tail -2
echo "--- a quien apunta ahora ---"
grep -A1 '<server>' /var/ossec/etc/ossec.conf | head -2
/var/ossec/bin/wazuh-control start 2>&1 | tail -2
"""


def paso4():
    t0 = time.time()
    anota("7 · La instalación que sí funciona: purgar y fijar",
          "¿Cuál es la secuencia correcta?",
          "apt-get purge -y wazuh-agent && rm -rf /var/ossec\n"
          'WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \\\n'
          "  apt-get install -y -o Dpkg::Options::=--force-confnew wazuh-agent=4.9.2-1",
          vic(LIMPIA),
          nota="Dos cosas que no son opcionales: **purgar** (el paquete a medio configurar hay "
               "que sacarlo entero) y `--force-confnew` (o vuelve a pararse en la misma "
               "pregunta).")

    espera = None
    for _ in range(60):
        if victima_activa():
            espera = round(time.time() - t0, 1)
            break
        time.sleep(2)
    anota("8 · Cuánto tarda en aparecer como activo",
          "Desde que empieza la instalación limpia, ¿cuándo lo ve el manager?",
          "docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l",
          agentes() + (f"\n\n[medido: {espera} s]" if espera
                       else "\n\n[NO llegó a Active en 120 s]"))

    anota("9 · Lo que queda guardado en el manager",
          "¿Qué es «estar enrolado», en concreto?",
          "docker exec lab-wazuh-manager cat /var/ossec/etc/client.keys",
          mgr("cat /var/ossec/etc/client.keys"),
          nota="Cuatro campos: id, nombre, IP permitida y la **clave compartida**. Eso es todo. "
               "El puerto 1515 solo sirve para entregar esa línea; a partir de ahí el agente "
               "habla por el 1514.")
    anota("10 · Y la misma línea, del lado del agente", "¿Tiene el agente lo mismo?",
          "docker exec lab-wazuh-victima cat /var/ossec/etc/client.keys",
          vic("cat /var/ossec/etc/client.keys"))


# ══ 5 · el evento que no llega ═════════════════════════════════════════════════════════
def paso5():
    antes = alertas()
    o = vic("logger -p auth.info 'PRUEBA: intento de sudo del becario'; "
            "echo \"logger termino con codigo $?\"; ls -la /var/log/auth.log 2>&1")
    time.sleep(15)
    anota("11 · ⛔ Provoco un evento y no llega nada",
          "El agente está activo. Provoco un evento. ¿Aparece?",
          "docker exec lab-wazuh-victima logger -p auth.info 'PRUEBA: intento de sudo'",
          o + f"\n\n[alertas en el manager: {antes} antes, {alertas()} después]",
          nota="El agente funciona y `logger` no se queja. Pero no hay nada que leer: sin "
               "syslog, `logger` escribe al vacío y `/var/log/auth.log` no existe. **El agente "
               "no inventa datos: lee ficheros.** Sin ficheros, es un punto ciego.")


PREPARAR = """export DEBIAN_FRONTEND=noninteractive
apt-get install -y -qq openssh-server rsyslog sshpass >/dev/null 2>&1
mkdir -p /run/sshd
id becario >/dev/null 2>&1 || useradd -m -s /bin/bash becario
echo 'becario:becario123' | chpasswd
(service rsyslog start >/dev/null 2>&1 || rsyslogd) ; /usr/sbin/sshd
sleep 3
echo "sshd:    $(pgrep -c sshd) proceso(s)"
echo "rsyslog: $(pgrep -c rsyslogd) proceso(s)"
ls -l /var/log/auth.log 2>&1
"""

# Un intento de autenticación FALLIDO de verdad, contra la propia víctima y contra nada más.
# `logger` no vale: escribe una línea que ningún decoder reconoce, así que no genera alerta
# aunque llegue al manager. Esto sí lo reconoce el motor de reglas.
FALLO_LOGIN = """sshpass -p 'contrasena-mala' ssh -o StrictHostKeyChecking=no \
  -o ConnectTimeout=5 becario@127.0.0.1 true 2>&1 | tail -1
echo '--- lo que queda en auth.log ---'
tail -2 /var/log/auth.log
"""

# El bloque que hay que añadirle al agente, y el aviso de cómo NO insertarlo.
ANADIR = """python3 - <<'EOF'
from pathlib import Path
p = Path('/var/ossec/etc/ossec.conf'); s = p.read_text()
bloque = '''  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>

</ossec_config>'''
i = s.index('</ossec_config>')          # SOLO el primero: el fichero tiene varios cierres
p.write_text(s[:i] + bloque + s[i + len('</ossec_config>'):])
EOF
echo "ficheros vigilados ahora: $(grep -c '<location>' /var/ossec/etc/ossec.conf)"
/var/ossec/bin/wazuh-control restart >/dev/null 2>&1
sleep 8
grep -i 'auth.log' /var/ossec/logs/ossec.log | tail -1
"""


def alertas_de_authlog():
    """Solo las que vienen de `auth.log`.

    ⛔ Contar el TOTAL de alertas del manager no vale: sube por su cuenta (dpkg, rootcheck, el
    propio agente arrancando). En la primera corrida eso dio «llegaron 2 alertas» cuando ninguna
    era del evento que yo había provocado."""
    s = mgr("grep -c '/var/log/auth.log' /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 0")
    m = re.findall(r"\d+", s)
    return int(m[-1]) if m else 0


def paso6():
    anota("12 · Le doy algo que leer", "¿Qué le faltaba a la máquina?",
          "apt-get install -y openssh-server rsyslog && rsyslogd && /usr/sbin/sshd",
          vic(PREPARAR),
          nota="Ahora sí existe `/var/log/auth.log`.")

    antes = alertas_de_authlog()
    t0 = time.time()
    o = vic(FALLO_LOGIN)
    llego = None
    for _ in range(30):
        if alertas_de_authlog() > antes:
            llego = round(time.time() - t0, 1)
            break
        time.sleep(1)
    anota("13 · ⛔ Y SIGUE sin llegar",
          "Ya hay `auth.log` y provoco un fallo de autenticación de verdad. ¿Ahora sí?",
          "sshpass -p 'contrasena-mala' ssh becario@127.0.0.1",
          o + f"\n\n[alertas desde auth.log: {antes} → {alertas_de_authlog()}"
              + (f"  ·  llegó en {llego} s]" if llego else "  ·  NADA en 30 s]"),
          nota="El fallo está escrito en `auth.log`, con el formato exacto que Wazuh reconoce. "
               "Y no llega. El problema ya no es el evento.")


def paso7():
    anota("14 · Por qué: el agente no lee ese fichero",
          "¿Qué ficheros está vigilando el agente, exactamente?",
          "docker exec lab-wazuh-victima grep '<location>' /var/ossec/etc/ossec.conf",
          vic("grep '<location>' /var/ossec/etc/ossec.conf"),
          nota="Ahí está. **La lista de ficheros del agente se decide al INSTALARLO**, mirando "
               "qué hay en la máquina en ese momento. Cuando instalé el agente, `auth.log` no "
               "existía todavía: lo creé después, con rsyslog. Así que el agente ni lo mira. "
               "El orden importa.")

    anota("15 · Se lo digo yo",
          "¿Cómo se le añade un fichero a vigilar?",
          "<localfile>  <log_format>syslog</log_format>  "
          "<location>/var/log/auth.log</location>  </localfile>",
          vic(ANADIR),
          nota="⚠️ Si lo insertas con `sed` sustituyendo `</ossec_config>`, se te mete **varias "
               "veces**: el fichero tiene más de un cierre de bloque. Solo el primero.")

    # ⛔ HAY QUE ESPERAR. Al reiniciar, el agente vuelve a hacer el saludo con el manager y
    # tarda otros ~25 s en darse por activo. Si provocas el evento antes, no llega y te crees
    # que el cambio de configuración no ha servido. Pasó en la corrida del 2026-08-24.
    espera_reconexion = None
    t_r = time.time()
    for _ in range(40):
        if victima_activa():
            espera_reconexion = round(time.time() - t_r, 1)
            break
        time.sleep(3)
    anota("15b · Y hay que esperar a que vuelva",
          "Tras reiniciar el agente, ¿puedo probar ya?",
          "docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l",
          agentes() + (f"\n\n[el agente tardó {espera_reconexion} s en volver a estar activo]"
                       if espera_reconexion else "\n\n[NO volvió en 120 s]"),
          nota="Tocar la configuración obliga a reiniciar, y reiniciar cuesta otro saludo con el "
               "manager. Si pruebas antes de que vuelva, no llega nada y te crees que el cambio "
               "no ha servido.")


    antes = alertas_de_authlog()
    t0 = time.time()
    o = vic(FALLO_LOGIN)
    llego = None
    for _ in range(45):
        if alertas_de_authlog() > antes:
            llego = round(time.time() - t0, 1)
            break
        time.sleep(1)
    anota("16 · Ahora sí: el circuito cerrado",
          "El mismo fallo de login, con el agente mirando el fichero. ¿Cuánto tarda?",
          "sshpass -p 'contrasena-mala' ssh becario@127.0.0.1",
          o + f"\n\n[alertas desde auth.log: {antes} → {alertas_de_authlog()}"
              + (f"  ·  llegó en {llego} s]" if llego else "  ·  NADA en 45 s]"))

    anota("17 · Qué le llegó exactamente al manager",
          "¿Qué guarda el manager de ese evento?",
          "docker exec lab-wazuh-manager tail -1 /var/ossec/logs/alerts/alerts.json",
          mgr("grep '/var/log/auth.log' /var/ossec/logs/alerts/alerts.json | tail -1 | "
              "python3 -c \""
              "import sys,json;d=json.load(sys.stdin);"
              "print('regla      ', d['rule']['id'], '- nivel', d['rule']['level']);"
              "print('descripcion:', d['rule']['description']);"
              "print('agente     :', d['agent']['id'], d['agent']['name']);"
              "print('fichero    :', d.get('location'));"
              "print('texto      :', d.get('full_log','')[:110])\""),
          nota="Regla, nivel, agente, fichero de origen y la línea entera. Eso es lo que el "
               "manager guarda de cada evento, y de ahí sale todo lo que se ve en el panel.")



def escribir():
    RAIZ.mkdir(parents=True, exist_ok=True)
    doc = ["# Pruebas ejecutadas — Wazuh lección 3: tu primer agente", "",
           "> Salida **literal** del laboratorio de esta máquina. La genera",
           "> `investigacion/pruebas_wazuh_03.py`, que **recrea la víctima** antes de empezar:",
           "> lo que se mide es un montaje desde cero, no un contenedor con intentos encima.",
           "> ⛔ Lo que no esté aquí no puede salir en pantalla (canon: ninguna cifra inventada).",
           "", "**Manager del laboratorio:**", "", "```",
           mgr("/var/ossec/bin/wazuh-control info"), "```", ""]
    for b in BLOQUES:
        doc += ["---", "", f"## {b['titulo']}", "", f"**La pregunta:** {b['pregunta']}", "",
                "```console", f"$ {b['orden']}", b["salida"], "```", ""]
        if b["nota"]:
            doc += ["> " + b["nota"].replace("\n", "\n> "), ""]
    # ⛔ Una corrida con bloques vacíos NO pisa el SALIDA.md bueno que ya esté en disco.
    destino = RAIZ / ("SALIDA.md" if not FALLOS else "SALIDA.FALLIDA.md")
    destino.write_text("\n".join(doc), encoding="utf-8")
    print(f"[{'ok' if not FALLOS else 'REVISAR'}] {destino}")
    for f in FALLOS:
        print("   ⚠️ bloque sin salida:", f)


if __name__ == "__main__":
    paso0(); paso1(); paso2(); paso3(); paso4(); paso5(); paso6(); paso7(); escribir()
