# Una línea de texto y 3 fases: cómo Wazuh decide que hay una alerta — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina · dentro del manager

```console
$ /var/ossec/bin/wazuh-logtest

Starting wazuh-logtest v4.9.2
Type one log per line
```

## 2. en mi máquina · la línea cruda

```console
Aug 27 16:30:01 victima sshd[15722]:
  Failed password for becario
  from 127.0.0.1 port 39010 ssh2
```

## 3. en mi máquina · Phase 1: pre-decoding

```console
timestamp:     'Aug 27 16:30:01'
hostname:      'victima'
program_name:  'sshd'
```

## 4. en mi máquina · Phase 2: decoding

```console
name:     'sshd'
dstuser:  'becario'
srcip:    '127.0.0.1'
srcport:  '39010'
```

## 5. en mi máquina · Phase 3: filtering (rules)

```console
id:           '5760'
level:        '5'
description:  'sshd: authentication failed.'
groups:       ['syslog','sshd','authentication_failed']

**Alert to be generated.
```

## 6. en mi máquina · lo que venía pegado a la regla 5760

```console
mitre.id:         ['T1110.001', 'T1021.004']
mitre.technique:  ['Password Guessing', 'SSH']
pci_dss:          ['10.2.4', '10.2.5']
gdpr:             ['IV_35.7.d', 'IV_32.2']
hipaa:            ['164.312.b']
nist_800_53:      ['AU.14', 'AC.7']
```

## 7. en mi máquina · una línea que nadie espera

```console
Aug 27 16:31:02 victima cafetera[42]:
  nivel de agua bajo, quedan 2 tazas
```

## 8. en mi máquina · Phase 1, igual que antes

```console
timestamp:     'Aug 27 16:31:02'
hostname:      'victima'
program_name:  'cafetera'
```

## 9. en mi máquina · Phase 2: decoding

```console
No decoder matched.
```

## 10. en mi máquina · el motivo, en el log del agente

```console
wazuh-logcollector: SIGNAL [(15)-(Terminated)]
  Received. Exit Cleaning...

ERROR: Another instance is locking this process.
remove /var/ossec/var/start-script-lock
```

## 11. en mi máquina · lo que el agente ya había mandado

```console
ficheros vigilados   1006
paquetes instalados   228
procesos               60
puertos abiertos        4
```
