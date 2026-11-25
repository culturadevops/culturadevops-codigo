# Pruebas ejecutadas — Wazuh lección 3: tu primer agente

> Salida **literal** del laboratorio de esta máquina. La genera
> `investigacion/pruebas_wazuh_03.py`, que **recrea la víctima** antes de empezar:
> lo que se mide es un montaje desde cero, no un contenedor con intentos encima.
> ⛔ Lo que no esté aquí no puede salir en pantalla (canon: ninguna cifra inventada).

**Manager del laboratorio:**

```
WAZUH_VERSION="v4.9.2"
WAZUH_REVISION="40921"
WAZUH_TYPE="server"
```

---

## 1 · De qué partimos: un Ubuntu pelado

**La pregunta:** ¿Qué hay en la máquina que vamos a vigilar, antes de tocar nada?

```console
$ docker exec lab-wazuh-victima sh -c '...'
PRETTY_NAME="Ubuntu 24.04.4 LTS"
---
ls: cannot access '/var/log/auth.log': No such file or directory
---
ls: cannot access '/var/ossec/bin': No such file or directory
```

> Ni agente ni `auth.log`. Un `ubuntu:24.04` no trae syslog: el fichero que todo el mundo da por hecho **no existe**.

---

## 2 · Y qué ve el manager

**La pregunta:** ¿Cuántos agentes hay ahora mismo?

```console
$ docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l

Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), IP: 127.0.0.1, Active/Local

List of agentless devices:
```

---

## 3 · El repositorio y la versión que ofrece

**La pregunta:** Si escribes `apt install wazuh-agent`, ¿qué versión te instala?

```console
$ apt-cache policy wazuh-agent
  Installed: (none)
  Candidate: 4.14.7-1
```

> El repositorio siempre ofrece la ÚLTIMA. El manager de este laboratorio es la 4.9.2.

---

## 4 · ⛔ Sin fijar la versión, el manager lo rechaza

**La pregunta:** ¿Qué pasa si instalas el agente sin decir qué versión quieres?

```console
$ apt-get install -y wazuh-agent      # sin versión
/var/ossec/bin/wazuh-control start
grep ERROR /var/ossec/logs/ossec.log
2026/08/24 21:00:18 wazuh-agentd: ERROR: Agent version must be lower or equal to manager version (from manager)
2026/08/24 21:00:18 wazuh-agentd: ERROR: Unable to add agent (from manager)
2026/08/24 21:00:28 wazuh-agentd: ERROR: Agent version must be lower or equal to manager version (from manager)
2026/08/24 21:00:28 wazuh-agentd: ERROR: Unable to add agent (from manager)
```

> Límite duro de Wazuh: **el agente nunca puede ser más nuevo que el manager**. Y el mensaje no sale en la pantalla del `apt`: hay que ir al registro del agente.

---

## 5 · Y en el manager, nada

**La pregunta:** ¿Se enroló de todas formas?

```console
$ docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l

Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), IP: 127.0.0.1, Active/Local

List of agentless devices:
```

---

## 6 · ⛔ Y arreglarlo no es simplemente reinstalar

**La pregunta:** Fijo la versión encima de la instalación mala. ¿Ya está?

```console
$ apt-get install -y --allow-downgrades wazuh-agent=4.9.2-1
*** wazuh-agent.service (Y/I/N/O/D/Z) [default=N] ? dpkg: error processing package wazuh-agent (--configure):
 end of file on stdin at conffile prompt
Errors were encountered while processing:
 wazuh-agent
E: Sub-process /usr/bin/dpkg returned an error code (1)
--- estado del paquete ---
iU  wazuh-agent    4.9.2-1      amd64     
--- a quien apunta ossec.conf ---
    <server>
      <address>MANAGER_IP</address>
```

> `dpkg` se para en una pregunta sobre el fichero de servicio que dejó la versión nueva, no hay nadie para contestarla, y el paquete se queda en **`iU`**: desempaquetado y SIN configurar. Y quien lee `WAZUH_MANAGER` y escribe `ossec.conf` es justo el paso de configuración que no llegó a correr. Por eso sigue poniendo `MANAGER_IP`.

---

## 7 · La instalación que sí funciona: purgar y fijar

**La pregunta:** ¿Cuál es la secuencia correcta?

```console
$ apt-get purge -y wazuh-agent && rm -rf /var/ossec
WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \
  apt-get install -y -o Dpkg::Options::=--force-confnew wazuh-agent=4.9.2-1
paquetes wazuh tras la purga: 0
Unpacking wazuh-agent (4.9.2-1) ...
Setting up wazuh-agent (4.9.2-1) ...
--- a quien apunta ahora ---
    <server>
      <address>wazuh.manager</address>
Started wazuh-modulesd...
Completed.
```

> Dos cosas que no son opcionales: **purgar** (el paquete a medio configurar hay que sacarlo entero) y `--force-confnew` (o vuelve a pararse en la misma pregunta).

---

## 8 · Cuánto tarda en aparecer como activo

**La pregunta:** Desde que empieza la instalación limpia, ¿cuándo lo ve el manager?

```console
$ docker exec lab-wazuh-manager /var/ossec/bin/agent_control -l

Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), IP: 127.0.0.1, Active/Local
   ID: 004, Name: victima, IP: any, Active

List of agentless devices:

[medido: 24.7 s]
```

---

## 9 · Lo que queda guardado en el manager

**La pregunta:** ¿Qué es «estar enrolado», en concreto?

```console
$ docker exec lab-wazuh-manager cat /var/ossec/etc/client.keys
004 victima any 69f9c71cc02ec8a43910d7e67e35b587f69f4f4e96a0bea3dcc7b85d488a90fb
```

> Cuatro campos: id, nombre, IP permitida y la **clave compartida**. Eso es todo. El puerto 1515 solo sirve para entregar esa línea; a partir de ahí el agente habla por el 1514.

---

## 10 · Y la misma línea, del lado del agente

**La pregunta:** ¿Tiene el agente lo mismo?

```console
$ docker exec lab-wazuh-victima cat /var/ossec/etc/client.keys
004 victima any 69f9c71cc02ec8a43910d7e67e35b587f69f4f4e96a0bea3dcc7b85d488a90fb
```

---

## 11 · ⛔ Provoco un evento y no llega nada

**La pregunta:** El agente está activo. Provoco un evento. ¿Aparece?

```console
$ docker exec lab-wazuh-victima logger -p auth.info 'PRUEBA: intento de sudo'
logger termino con codigo 0
ls: cannot access '/var/log/auth.log': No such file or directory

[alertas en el manager: 462 antes, 464 después]
```

> El agente funciona y `logger` no se queja. Pero no hay nada que leer: sin syslog, `logger` escribe al vacío y `/var/log/auth.log` no existe. **El agente no inventa datos: lee ficheros.** Sin ficheros, es un punto ciego.

---

## 12 · Le doy algo que leer

**La pregunta:** ¿Qué le faltaba a la máquina?

```console
$ apt-get install -y openssh-server rsyslog && rsyslogd && /usr/sbin/sshd
sshd:    1 proceso(s)
rsyslog: 1 proceso(s)
-rw-r----- 1 syslog adm 175 Aug 24 21:01 /var/log/auth.log
rsyslogd: imklog: cannot open kernel log (/proc/kmsg): Operation not permitted.
rsyslogd: activation of module imklog failed [v8.2312.0 try https://www.rsyslog.com/e/2145 ]
```

> Ahora sí existe `/var/log/auth.log`.

---

## 13 · ⛔ Y SIGUE sin llegar

**La pregunta:** Ya hay `auth.log` y provoco un fallo de autenticación de verdad. ¿Ahora sí?

```console
$ sshpass -p 'contrasena-mala' ssh becario@127.0.0.1
Permission denied, please try again.
--- lo que queda en auth.log ---
2026-08-24T21:02:01.613481+00:00 victima sshd[9143]: Failed password for becario from 127.0.0.1 port 50734 ssh2
2026-08-24T21:02:02.131644+00:00 victima sshd[9143]: Connection closed by authenticating user becario 127.0.0.1 port 50734 [preauth]

[alertas desde auth.log: 2 → 2  ·  NADA en 30 s]
```

> El fallo está escrito en `auth.log`, con el formato exacto que Wazuh reconoce. Y no llega. El problema ya no es el evento.

---

## 14 · Por qué: el agente no lee ese fichero

**La pregunta:** ¿Qué ficheros está vigilando el agente, exactamente?

```console
$ docker exec lab-wazuh-victima grep '<location>' /var/ossec/etc/ossec.conf
    <location>/var/ossec/logs/active-responses.log</location>
    <location>/var/log/dpkg.log</location>
```

> Ahí está. **La lista de ficheros del agente se decide al INSTALARLO**, mirando qué hay en la máquina en ese momento. Cuando instalé el agente, `auth.log` no existía todavía: lo creé después, con rsyslog. Así que el agente ni lo mira. El orden importa.

---

## 15 · Se lo digo yo

**La pregunta:** ¿Cómo se le añade un fichero a vigilar?

```console
$ <localfile>  <log_format>syslog</log_format>  <location>/var/log/auth.log</location>  </localfile>
ficheros vigilados ahora: 3
```

> ⚠️ Si lo insertas con `sed` sustituyendo `</ossec_config>`, se te mete **varias veces**: el fichero tiene más de un cierre de bloque. Solo el primero.

---

## 16 · Ahora sí: el circuito cerrado

**La pregunta:** El mismo fallo de login, con el agente mirando el fichero. ¿Cuánto tarda?

```console
$ sshpass -p 'contrasena-mala' ssh becario@127.0.0.1
Permission denied, please try again.
--- lo que queda en auth.log ---
2026-08-24T21:03:45.219929+00:00 victima sshd[11463]: Failed password for becario from 127.0.0.1 port 39730 ssh2
2026-08-24T21:03:46.126840+00:00 victima sshd[11463]: Connection closed by authenticating user becario 127.0.0.1 port 39730 [preauth]

[alertas desde auth.log: 2 → 2  ·  NADA en 45 s]
```

---

## 17 · Qué le llegó exactamente al manager

**La pregunta:** ¿Qué guarda el manager de ese evento?

```console
$ docker exec lab-wazuh-manager tail -1 /var/ossec/logs/alerts/alerts.json
regla       5760 - nivel 5
descripcion: sshd: authentication failed.
agente     : 003 victima
fichero    : /var/log/auth.log
texto      : 2026-08-24T20:57:09.570805+00:00 victima sshd[21544]: Failed password for becario from 127.0.0.1 port 60878 ss
```

> Regla, nivel, agente, fichero de origen y la línea entera. Eso es lo que el manager guarda de cada evento, y de ahí sale todo lo que se ve en el panel.
