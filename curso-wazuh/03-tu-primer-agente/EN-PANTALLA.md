# El agente decía «Active» y mentía: tu primer agente de Wazuh — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. la víctima, antes de tocar nada

```console
$ cat /etc/os-release | grep PRETTY
PRETTY_NAME="Ubuntu 24.04.4 LTS"

$ ls -la /var/log/auth.log
ls: cannot access '/var/log/auth.log': No such file or directory

$ ls /var/ossec/bin
ls: cannot access '/var/ossec/bin': No such file or directory
```

## 2. qué versión te va a instalar

```console
$ apt-cache policy wazuh-agent
  Installed: (none)
  Candidate: 4.14.7-1
```

## 3. el rechazo, en el registro del agente

```console
$ apt-get install -y wazuh-agent      # sin versión
$ grep ERROR /var/ossec/logs/ossec.log | tail -2

wazuh-agentd: ERROR: Agent version must be lower or
  equal to manager version (from manager)
wazuh-agentd: ERROR: Unable to add agent (from manager)
```

## 4. dpkg se para en una pregunta

```console
$ apt-get install -y --allow-downgrades wazuh-agent=4.9.2-1

*** wazuh-agent.service (Y/I/N/O/D/Z) [default=N] ?
dpkg: error processing package wazuh-agent (--configure):
  end of file on stdin at conffile prompt
```

## 5. el estado del paquete, y lo que significa

```console
$ dpkg -l wazuh-agent
iU  wazuh-agent    4.9.2-1    amd64

$ grep -A1 '<server>' /var/ossec/etc/ossec.conf
    <server>
      <address>MANAGER_IP</address>
```

## 6. la secuencia que sí funciona

```console
$ apt-get purge -y wazuh-agent && rm -rf /var/ossec

$ WAZUH_MANAGER="wazuh.manager" WAZUH_AGENT_NAME="victima" \
  apt-get install -y \
    -o Dpkg::Options::=--force-confnew wazuh-agent=4.9.2-1

Setting up wazuh-agent (4.9.2-1) ...
      <address>wazuh.manager</address>
```

## 7. ya está en la lista

```console
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh.manager (server), Active/Local
   ID: 005, Name: victima, IP: any, Active
```

## 8. qué es estar enrolado, en concreto

```console
$ cat /var/ossec/etc/client.keys
005  victima  any  <clave de 64 caracteres>
```

## 9. ahora sí hay registro, y hay fallo

```console
$ apt-get install -y openssh-server rsyslog
$ sshpass -p 'contrasena-mala' ssh becario@127.0.0.1
Permission denied, please try again.

$ tail -1 /var/log/auth.log
victima sshd[9143]: Failed password for becario
  from 127.0.0.1 port 50734 ssh2
```

## 10. qué mira el agente, exactamente

```console
$ grep '<location>' /var/ossec/etc/ossec.conf
    <location>/var/ossec/logs/active-responses.log</location>
    <location>/var/log/dpkg.log</location>
```

## 11. añadirle el fichero que faltaba

```console
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>

ficheros vigilados ahora: 3
```

## 12. lo que le llegó al manager

```console
Rule: 5760 (level 5)
descripcion: 'sshd: authentication failed.'
agente     : 005 victima
fichero    : /var/log/auth.log
texto      : victima sshd: Failed password for becario
```
