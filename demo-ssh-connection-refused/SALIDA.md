# SALIDA — SSH: connection refused en el puerto 22 (cultura-devops)

> Corrida del 2026-10-20 16:45. Dos contenedores Debian trixie en una red de Docker propia; OpenSSH_10.0p2 Debian-7+deb13u4, OpenSSL 3.5.7 9 Jun 2026.

```
### 1 · El error
$ ssh ana@servidor
ssh: connect to host servidor port 22: Connection refused

### 2 · ¿Hay algo escuchando en el 22?
$ nc -zv servidor 22
nc: connect to servidor (192.168.192.2) port 22 (tcp) failed: Connection refused
servidor$ ss -tlnp
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096      127.0.0.11:44913      0.0.0.0:*          
servidor$ pgrep -a sshd
(nada)

### 3 · Arrancar el servicio
servidor$ /usr/sbin/sshd   # en una máquina normal: sudo systemctl start ssh
servidor$ ss -tlnp | grep sshd
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=40,fd=6))
LISTEN 0      128             [::]:22            [::]:*    users:(("sshd",pid=40,fd=7))
$ ssh ana@servidor hostname
Warning: Permanently added 'servidor' (ED25519) to the list of known hosts.
servidor

### 4 · sshd escucha en otro puerto
servidor$ grep ^Port /etc/ssh/sshd_config
Port 2222
servidor$ ss -tlnp | grep sshd
LISTEN 0      128          0.0.0.0:2222       0.0.0.0:*    users:(("sshd",pid=80,fd=6))
LISTEN 0      128             [::]:2222          [::]:*    users:(("sshd",pid=80,fd=7))
$ ssh ana@servidor hostname
ssh: connect to host servidor port 22: Connection refused
$ ssh -p 2222 ana@servidor hostname
servidor

### 5 · sshd solo escucha en localhost
servidor$ grep ^ListenAddress /etc/ssh/sshd_config
ListenAddress 127.0.0.1
servidor$ ss -tlnp | grep sshd
LISTEN 0      128        127.0.0.1:22         0.0.0.0:*    users:(("sshd",pid=126,fd=6))
$ ssh ana@servidor hostname
ssh: connect to host servidor port 22: Connection refused

### 6 · Un firewall que rechaza
servidor$ iptables -A INPUT -p tcp --dport 22 -j REJECT --reject-with tcp-reset
$ ssh ana@servidor hostname
ssh: connect to host servidor port 22: Connection refused
servidor$ ss -tlnp | grep sshd   # sshd sí está escuchando
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=152,fd=6))
LISTEN 0      128             [::]:22            [::]:*    users:(("sshd",pid=152,fd=7))

### 7 · Un firewall que descarta: otro error
servidor$ iptables -A INPUT -p tcp --dport 22 -j DROP
$ time ssh -o ConnectTimeout=5 ana@servidor hostname
ssh: connect to host servidor port 22: Connection timed out
(tardó 5 s)

### 8 · Una IP donde no hay nadie
$ ssh ana@192.168.192.200 hostname
ssh: connect to host 192.168.192.200 port 22: No route to host

### 9 · Todo en orden
$ nc -zv servidor 22 && ssh ana@servidor hostname
Connection to servidor (192.168.192.2) 22 port [tcp/ssh] succeeded!
servidor
```
