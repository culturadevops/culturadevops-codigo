# SALIDA — CrowdSec vs Fail2ban (vídeo 341)

Generado 2026-10-12 23:04 UTC con `python correr.py`. Los fallos se escriben en el auth.log de los dos servidores a la vez (misma línea que deja sshd); el bloqueo se comprueba con una conexión TCP real.

## 1 · Versiones y valores por defecto

### versiones

`$ fail2ban-server --version; crowdsec -version; crowdsec-firewall-bouncer -V`

```
Fail2Ban v1.0.2
crowdsec version: v1.8.1-debian-pragmatic-amd64-909b5157
bouncer version: v0.0.36-debian-pragmatic-amd64-4c315193cd4f19e3937cdee2f15183ec4d602f56
```

### Fail2ban, jail sshd por defecto

`$ fail2ban-client get sshd maxretry|findtime|bantime; jail.conf ignoreip`

```
maxretry 5
findtime 600
bantime  600
92:#ignoreip = 127.0.0.1/8 ::1
```

### lo que hay que escribir para Fail2ban

`$ cat /etc/fail2ban/jail.d/lab.local`

```
[sshd]
enabled = true
backend = polling
logpath = /var/log/auth.log
banaction = iptables-multiport
```

### CrowdSec, escenarios de SSH por defecto

`$ grep capacity|leakspeed /etc/crowdsec/scenarios/ssh-*bf.yaml; profiles.yaml`

```
ssh-bf: leakspeed: "10s" capacity: 5 leakspeed: 10s capacity: 5 
ssh-slow-bf: leakspeed: "60s" capacity: 10 leakspeed: 60s capacity: 10 
   duration: 4h
6 escenarios de SSH instalados
```

### lo que hay que escribir para CrowdSec

`$ cscli collections install crowdsecurity/linux crowdsecurity/sshd; cat acquis.d/ssh.yaml`

```
filenames:
  - /var/log/auth.log
labels:
  type: syslog
crowdsecurity/sshd                   ✔️  enabled  0.9      /etc/crowdsec/collections/sshd.yaml
```

### el bloqueador de CrowdSec ya está enganchado

`$ iptables -S | grep CROWDSEC; cscli bouncers list`

```
-N CROWDSEC_CHAIN
-A INPUT -j CROWDSEC_CHAIN
"type": "crowdsec-firewall-bouncer"
```

## 2 · Una IP privada: ¿la banean?

### ráfaga desde una IP privada (10.79.0.50)

`$ 10 fallos desde 10.79.0.50, uno cada 1 s`

```
línea escrita en los dos auth.log:
  Oct 12 22:59:39 servidor sshd[4501]: Failed password for root from 10.79.0.50 port 50001 ssh2

   0.1 s  fallo  1
   1.2 s  fallo  2
   2.3 s  fallo  3
  …
   8.1 s  fallo  9
   9.3 s  fallo 10

Fail2ban  baneada a los 5.7 s, tras 6 fallos
CrowdSec  baneada a los 6.3 s, tras 7 fallos
```

### lo que leyó CrowdSec

`$ cscli metrics show acquisition`

```
| Source                 | Lines read | Lines parsed | Lines unparsed | Lines poured to bucket | Lines whitelisted |
| file:/var/log/auth.log | 10         | 10           | -              | 33                     | -                 |
```

## 3 · Ráfaga: 10 fallos, uno por segundo

### ráfaga desde 10.79.0.51

`$ 10 fallos desde 10.79.0.51, uno cada 1 s`

```
línea escrita en los dos auth.log:
  Oct 12 23:00:00 servidor sshd[4501]: Failed password for root from 10.79.0.51 port 50001 ssh2

   0.1 s  fallo  1
   1.3 s  fallo  2
   2.4 s  fallo  3
  …
   8.3 s  fallo  9
   9.2 s  fallo 10

Fail2ban  baneada a los 5.8 s, tras 6 fallos
CrowdSec  baneada a los 6.0 s, tras 6 fallos
```

### la decisión de CrowdSec

`$ cscli decisions list`

```
| ID |  Source  |  Scope:Value  |        Reason        | Action | Country | AS | Events | expiration | Alert ID |
| 2  | crowdsec | Ip:10.79.0.51 | crowdsecurity/ssh-bf | ban    |         |    | 6      | 3h59m53s   | 2        |
```

### la de Fail2ban

`$ fail2ban-client status sshd`

```
Status for the jail: sshd
|- Filter
|  |- Currently failed:	0
|  |- Total failed:	20
|  `- File list:	/var/log/auth.log
`- Actions
   |- Currently banned:	1
   |- Total banned:	2
   `- Banned IP list:	10.79.0.51
```

## 4 · El bloqueo es real (conexión TCP al 22)

### nc -z al puerto 22

`$ nc -z -w 3 <servidor> 22`

```
Fail2ban  desde 10.79.0.51 (baneada): sin respuesta
Fail2ban  desde 10.79.0.60 (limpia ): abierto
CrowdSec  desde 10.79.0.51 (baneada): sin respuesta
CrowdSec  desde 10.79.0.60 (limpia ): abierto
```

### la regla en el cortafuegos

`$ iptables -S | grep 10.79.0.51; ipset`

```
Fail2ban: -A f2b-sshd -s 10.79.0.51/32 -j REJECT --reject-with icmp-port-unreachable
CrowdSec: -N CROWDSEC_CHAIN
-A INPUT -j CROWDSEC_CHAIN
-A CROWDSEC_CHAIN -m set --match-set crowdsec-blacklists-0 src -m comment --comment "CrowdSec: crowdsec" -j DROP
Name: crowdsec-blacklists-0
10.79.0.51 timeout 14387
```

## 5 · Lento: un fallo cada 15 s

### lento desde 10.79.0.52

`$ 18 fallos desde 10.79.0.52, uno cada 15 s`

```
línea escrita en los dos auth.log:
  Oct 12 23:00:18 servidor sshd[4501]: Failed password for root from 10.79.0.52 port 50001 ssh2

   0.1 s  fallo  1
  15.6 s  fallo  2
  30.2 s  fallo  3
  …
 240.1 s  fallo 17
 255.3 s  fallo 18

Fail2ban  baneada a los 61.7 s, tras 5 fallos
CrowdSec  baneada a los 196.5 s, tras 14 fallos
```

### qué escenario lo cazó en CrowdSec

`$ cscli alerts list`

```
| ID |     value     |           reason          | country | as | decisions |      created_at      |   kind   |
| 3  | Ip:10.79.0.52 | crowdsecurity/ssh-slow-bf |         |    | ban:1     | 2026-10-12T23:00:18Z | crowdsec |
| 2  | Ip:10.79.0.51 | crowdsecurity/ssh-bf      |         |    | ban:1     | 2026-10-12T23:00:01Z | crowdsec |
| 1  | Ip:10.79.0.50 | crowdsecurity/ssh-bf      |         |    | ban:1     | 2026-10-12T22:59:39Z | crowdsec |
```

## 6 · Quitar un baneo

### Fail2ban

`$ fail2ban-client set sshd unbanip 10.79.0.51`

```
1
```

### CrowdSec

`$ cscli decisions delete --ip 10.79.0.51`

```
level=info msg="1 decision(s) deleted"
```

### vuelve a entrar

`$ nc -z -w 3 <servidor> 22 desde 10.79.0.51`

```
Fail2ban: abierto
CrowdSec: abierto
```

## 7 · Lo que pesa

### memoria (servidor con su herramienta, en reposo)

`$ docker stats --no-stream`

```
srv-f2b 15.41MiB / 15.36GiB
srv-cs 129.1MiB / 15.36GiB
```

### procesos

`$ ps -o rss,comm`

```
Fail2ban:
4800 sshd
23720 fail2ban-server
CrowdSec:
19740 crowdsec-firewa
 4848 sshd
181928 crowdsec
```

### tamaño de la imagen (Debian + sshd + herramienta)

`$ docker image inspect -f {{.Size}}`

```
lab-f2b   73.9 MB
lab-cs    226.7 MB
```

## 8 · Anexo: ¿con quién se conecta al arrancar?

### CrowdSec: registro de arranque

`$ grep -E 'Central API|community-blocklist' /var/log/crowdsec.log; online_api_credentials.yaml`

```
level=error msg="Machine is not enrolled in the console, can't synchronize with the console"
level=info msg="Start push to CrowdSec Central API (interval: 11s once, then 10s)"
level=info msg="Start sending metrics to CrowdSec Central API (interval: 28m28s once, then 30m0s)"
level=info msg="capi metrics: sending"
level=info msg="Starting community-blocklist update"
level=info msg="capi/community-blocklist : 0 explicit deletions"
url: https://api.crowdsec.net/
```

### Fail2ban: líneas con http o api en su registro

`$ grep -c -i -E 'http|api' /var/log/fail2ban.log`

```
0
```

## 9 · Anexo: solo la colección sshd, sin la de linux

### quitar crowdsecurity/linux

`$ cscli collections remove crowdsecurity/linux --force; cscli parsers list | grep -c syslog-logs`

```
disabling collections:crowdsecurity/linux

Run 'sudo systemctl reload crowdsec' for the new configuration to be effective.
0
```

### 8 fallos después

`$ cscli metrics show acquisition; cscli decisions list`

```
| Source                 | Lines read | Lines parsed | Lines unparsed | Lines poured to bucket | Lines whitelisted |
| file:/var/log/auth.log | 8          | 8            | -              | -                      | -                 |
No active decisions
```

### errores en el registro

`$ grep -c -i error /var/log/crowdsec.log`

```
2
```

## 10 · Anexo: otros servicios, reincidencia y tu propia IP

### Fail2ban: cárceles y filtros que trae

`$ grep -c '^\[' jail.conf; ls filter.d | wc -l`

```
cárceles: 91
filtros: 94
```

### Fail2ban: la cárcel de reincidentes

`$ grep -A12 '^\[recidive\]' jail.conf`

```
[recidive]
logpath  = /var/log/fail2ban.log
bantime  = 1w
findtime = 1d
[pam-generic]
logpath  = %(syslog_authpriv)s
```

### Fail2ban: tu propia IP fuera

`$ grep ignoreip jail.conf`

```
89:# "ignoreip" can be a list of IP addresses, CIDR masks or DNS hosts. Fail2ban
92:#ignoreip = 127.0.0.1/8 ::1
```

### CrowdSec: colecciones disponibles en su hub

`$ cscli collections list -a | grep -c crowdsecurity/`

```
colecciones: 96
escenarios: 160
```

### CrowdSec: bloqueos más largos para quien repite

`$ grep duration profiles.yaml`

```
7:   duration: 4h
8:#duration_expr: Sprintf('%dh', (GetDecisionsCount(Alert.GetValue()) + 1) * 4)
```

### CrowdSec: tu propia IP fuera

`$ cscli allowlists create casa; cscli allowlists add casa 198.51.100.7; cscli allowlists list`

```
allowlist 'casa' created successfully
added 1 values to allowlist casa
 Name  Description  Created at                Updated at                Managed by Console  Size 
 casa  mi IP        2026-10-12T23:11:07.939Z  2026-10-12T23:11:07.960Z  no                     1
```

## 11 · Anexo: Fail2ban en un Debian 12 recién instalado

### ¿hay rsyslog?

`$ dpkg -l rsyslog`

```
dpkg-query: no packages found matching rsyslog
```

### lo que activa el paquete de Debian

`$ cat /etc/fail2ban/jail.d/defaults-debian.conf`

```
[sshd]
enabled = true
```

### arrancar así, sin auth.log

`$ fail2ban-server -xf start`

```
fail2ban                [9]: ERROR   Failed during configuration: Have not found any log file for sshd jail
```
