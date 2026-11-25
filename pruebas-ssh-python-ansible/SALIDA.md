# SALIDA — Un comando en 50 servidores por SSH: Python o Ansible (cultura-devops 800, 2026-11-05)

Ejecutado el 2026-11-05 con `python correr.py levantar` y luego cada escenario. Las salidas sin editar están en `salidas/*.txt`;
aquí se copian. Laboratorio copiado del 682 de golandia (`canales/golandia/recursos/pruebas-cliente-ssh`).

## Versiones
```
$ python --version; python -c 'import asyncssh; print("asyncssh", asyncssh.__version__)'; ansible --version | head -1; ssh -V
Python 3.13.17
asyncssh 2.24.1
ansible [core 2.22.0]
OpenSSH_10.0p2 Debian-7+deb13u4, OpenSSL 3.5.7 9 Jun 2026
$ grep -vc '^#' /root/.ssh/known_hosts; wc -l < hosts-50.txt
150
50
```
- Docker 29.6.2. Red propia `cd800` (10.80.0.0/24). Todos los contenedores con `--rm`, prefijo `cd800-`.
- Servidores: `cd800-sshd:1` = alpine:3.22 + openssh-server 10.0_p1-r11, 16,8 MB. `--cpus 0.25 --memory 48m` cada uno.
  Cada contenedor genera sus claves de host al arrancar. Solo clave pública. Usuario `admin`.
- Máquina de control: `cd800-control:1` = python:3.13.17-slim + openssh-client + asyncssh 2.24.1 + ansible-core 2.22.0
  (265 MB), `--cpus 1 --memory 1g`. Las llaves de la demo se generan DENTRO de ese contenedor (no se toca ~/.ssh del equipo).
- `flota.py`: 76 líneas no vacías (asyncssh). `revisar.yml`: 7 líneas no vacías.
```
$ grep -cv '^\s*$' flota.py; grep -cv '^\s*$' revisar.yml
76
7
```

## El laboratorio
- 50 servidores s01…s50. La tarea `revisar` tarda 1 s y escribe `sNN disco 41%`.
- s13 «lleno»: escribe `disco 97%`, una línea en stderr y sale con 2.
- s46 llave mala: su authorized_keys tiene la llave pública de OTRO cliente.
- s48 congelado: `docker pause` → acepta la conexión TCP pero sshd nunca manda el saludo.
- s49 lento: `revisar` tarda 30 s.
- s50 apagado: `docker stop` → nadie contesta en su IP (10.80.0.60).
- known_hosts: `ssh-keyscan` de los 50 con todos sanos → 150 claves.
- «hosts-sanos.txt» = los 50 menos s46, s48, s49 y s50 (46 hosts; incluye s13).

## 1 · Uno solo, y el código de salida
```
$ cd /root && python flota.py -hosts s01.txt; echo "código de salida: $?"
s01      0    1.1s  s01 disco 41%
1 hosts · 1 ok · 0 con código distinto de 0 · 0 sin respuesta · 1.1s en total
código de salida: 0
$ cd /root && python flota.py -hosts s13.txt; echo "código de salida: $?"
s13      2    1.1s  s13 disco 97%
s13    stderr        revisar: disco casi lleno
1 hosts · 0 ok · 1 con código distinto de 0 · 0 sin respuesta · 1.1s en total
código de salida: 1
```
(flota sale con 0 si todo bien, 1 si algún host dio código distinto de 0, 2 si alguno no respondió.)

## 2 · Los 50 a la vez, con los que fallan (-p 50, conectar 3 s, comando 10 s)
```
$ cd /root && python flota.py -hosts hosts-50.txt -p 50; echo "código de salida: $?"
s01      0    1.2s  s01 disco 41%
…
s13      2    1.2s  s13 disco 97%
s13    stderr        revisar: disco casi lleno
…
s45      0    1.2s  s45 disco 41%
s46    ERR    0.1s  PermissionDenied: Permission denied for user admin on host s46
s47      0    1.2s  s47 disco 41%
s48    ERR    3.0s  no conectó en 3s
s49    ERR   10.2s  el comando no terminó en 10s
s50    ERR    3.0s  no conectó en 3s
50 hosts · 45 ok · 1 con código distinto de 0 · 4 sin respuesta · 10.2s en total
código de salida: 2
```
Un host malo no para a los demás: cada error se queda en su línea.

## 3 · Orden de la salida
```
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 50 -llegada > llegada.txt; head -6 llegada.txt
s43      0    1.2s  s43 disco 41%
s17      0    1.2s  s17 disco 41%
s05      0    1.2s  s05 disco 41%
s13      2    1.2s  s13 disco 97%
s13    stderr        revisar: disco casi lleno
s28      0    1.2s  s28 disco 41%
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 50 | head -6
s01      0    1.2s  s01 disco 41%
s02      0    1.2s  s02 disco 41%
s03      0    1.2s  s03 disco 41%
s04      0    1.2s  s04 disco 41%
s05      0    1.2s  s05 disco 41%
s06      0    1.2s  s06 disco 41%
```
`asyncio.as_completed` = orden de llegada; `asyncio.gather` = el orden de la lista.

## 4 · known_hosts: asyncssh comprueba la huella por defecto
```
$ cd /root && python flota.py -hosts s01.txt -known known_hosts_vacio; echo "código de salida: $?"
s01    ERR    0.0s  HostKeyNotVerifiable: Host key is not trusted for host s01
1 hosts · 0 ok · 0 con código distinto de 0 · 1 sin respuesta · 0.0s en total
código de salida: 2
```

## 5 · La trampa: asyncssh sin connect_timeout ni timeout del comando (-ingenuo)
```
$ time timeout 200  python flota.py -ingenuo -hosts s48.txt; echo "código de salida: $?"
s48    ERR  120.1s  ConnectionLost: Login timeout expired
1 hosts · 0 ok · 0 con código distinto de 0 · 1 sin respuesta · 120.1s en total

real	2m0.285s
user	0m0.107s
sys	0m0.034s
código de salida: 2
$ cd /root && python flota.py -ingenuo -hosts s49.txt
s49      0   30.1s  s49 disco 41%
1 hosts · 1 ok · 0 con código distinto de 0 · 0 sin respuesta · 30.1s en total
$ cd /root && python flota.py -ingenuo -hosts s50.txt
s50    ERR    3.1s  OSError: [Errno 113] Connect call failed ('10.80.0.60', 22)
1 hosts · 0 ok · 0 con código distinto de 0 · 1 sin respuesta · 3.1s en total
```
- s48: sin `connect_timeout`, asyncssh espera su `login_timeout` por defecto: `_DEFAULT_LOGIN_TIMEOUT = 120  # 2 minutes`
  (asyncssh/connection.py, línea 270 en 2.24.1). Dos minutos por un servidor congelado.
- s49: sin `timeout` en `run`, se espera los 30 s enteros.
- s50: el error a los ~3 s es del sistema (Errno 113, «no route to host»: nadie contesta en esa IP de la red local), no de un
  límite nuestro. En otra red podría tardar mucho más (no medido).

## 6 · Ansible: lo mismo, ad-hoc y con playbook (-f 50 -T 3)
```
$ cd /root && ansible all -m raw -a revisar -f 50 -T 3 > adhoc.txt 2>&1; echo "código de salida: $?"; grep -E '^s(01|13|46|48|49|50) ' adhoc.txt
código de salida: 4
s01 | CHANGED | rc=0 >>
s01 disco 41%
s13 | FAILED | rc=2 >>
s13 disco 97%
s46 | UNREACHABLE! => {
s48 | UNREACHABLE! => {
s50 | UNREACHABLE! => {
s49 | CHANGED | rc=0 >>
s49 disco 41%
$ cd /root && ansible-playbook revisar.yml -f 50 -T 3 > play.txt 2>&1; echo "código de salida: $?"; grep -E '^fatal' play.txt; grep -E '^s(01|13|46|48|49|50) ' play.txt
código de salida: 4
fatal: [s46]: UNREACHABLE! => {"changed": false, "msg": "Task failed: Failed to connect to the host via ssh: admin@s46: Permission denied (publickey).", "unreachable": true}
fatal: [s13]: FAILED! => {"changed": true, "msg": "non-zero return code", "rc": 2, "stderr": "Shared connection to s13 closed.\r\n", "stderr_lines": ["Shared connection to s13 closed."], "stdout": "s13 disco 97%\r\nrevisar: disco casi lleno\r\n", "stdout_lines": ["s13 disco 97%", "revisar: disco casi lleno"]}
fatal: [s48]: UNREACHABLE! => {"changed": false, "msg": "Task failed: Failed to connect to the host via ssh: Connection timed out during banner exchange\r\nConnection to 10.80.0.58 port 22 timed out", "unreachable": true}
fatal: [s50]: UNREACHABLE! => {"changed": false, "msg": "Task failed: Failed to connect to the host via ssh: ssh: connect to host s50 port 22: Connection timed out", "unreachable": true}
fatal: [s49]: FAILED! => {"changed": false, "msg": "Task failed: Timed out after 10 second(s).", "timedout": {"frame": "Configure `DISPLAY_TRACEBACK` to see a traceback on timeout errors.", "period": 10}}
s01                        : ok=1    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
s13                        : ok=0    changed=0    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0   
s46                        : ok=0    changed=0    unreachable=1    failed=0    skipped=0    rescued=0    ignored=0   
s48                        : ok=0    changed=0    unreachable=1    failed=0    skipped=0    rescued=0    ignored=0   
s49                        : ok=0    changed=0    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0   
s50                        : ok=0    changed=0    unreachable=1    failed=0    skipped=0    rescued=0    ignored=0
```
`revisar.yml`:
```yaml
- name: revisar la flota
  hosts: all
  gather_facts: false
  tasks:
    - name: revisar
      ansible.builtin.raw: revisar
      timeout: 10
```
- `-T 3` corta la conexión (s48 «during banner exchange», s50), como `connect_timeout` en asyncssh.
- En ad-hoc NO hay límite al comando: s49 se esperó entero y salió `CHANGED rc=0`. En el playbook, `timeout: 10` lo corta.
- `raw` pide terminal: el stderr de s13 llega MEZCLADO en stdout (con `\r\n`) y en stderr queda «Shared connection to s13 closed.».
  asyncssh, sin terminal, los da separados.
- Código de salida de Ansible: 4 (hay inalcanzables). flota: 2.

## 7 · ¿LLEGARON LOS DOS AL MISMO ESTADO? (antes de comparar nada)
`comparar.py`: flota.py `-json` y ansible-playbook con el callback `tree` (viene con ansible-core), host por host. Como `raw` mezcla
stderr en stdout, en el lado de Python se juntan stdout y stderr antes de comparar, y en Ansible se cambia `\r\n` por `\n`.
```
$ python comparar.py; echo "código de salida: $?"
python : {'error': 4, 'rc=0': 45, 'rc=2': 1}
ansible: {'error': 4, 'rc=0': 45, 'rc=2': 1}
hosts con el mismo estado y la misma salida: 50 de 50
código de salida: 0
```
Primera pasada (sin normalizar): 49 de 50, `DISTINTO s13` — la mezcla de stderr de `raw`, que es un hallazgo, no un fallo del banco.

## 8 · Tiempos (CRONOMETRADO, con el candado _logs/banco.lock)
flota.py: candado 09:00:21-09:03:38 (`correr.py tiempos`). En esa corrida, `time cd /root && ansible ...` cronometró el `cd`
(0,000 s): descartado. Ansible repetido con `correr.py tiempos_ansible`, candado 10:50:31-10:54:05 (otra corrida, mismo
laboratorio, sin reiniciar los contenedores). Los 46 sanos = los 50 menos s46, s48, s49 y s50; la tarea tarda 1 s en cada uno.
```
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 1 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 49.7s en total
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 1 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 49.4s en total
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 10 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 5.4s en total
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 10 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 5.4s en total
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 50 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 1.2s en total
$ cd /root && python flota.py -hosts hosts-sanos.txt -p 50 | tail -1
46 hosts · 45 ok · 1 con código distinto de 0 · 0 sin respuesta · 1.2s en total
$ cd /root && python flota.py -hosts hosts-50.txt -p 50 | tail -1
50 hosts · 45 ok · 1 con código distinto de 0 · 4 sin respuesta · 10.2s en total
$ cd /root && python flota.py -hosts hosts-50.txt -p 50 | tail -1
50 hosts · 45 ok · 1 con código distinto de 0 · 4 sin respuesta · 10.2s en total
```
```
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 5 > /dev/null

real	0m12.025s
user	0m1.950s
sys	0m0.734s
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 5 > /dev/null

real	0m10.541s
user	0m1.618s
sys	0m0.666s
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 10 > /dev/null

real	0m5.689s
user	0m1.415s
sys	0m0.607s
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 10 > /dev/null

real	0m5.639s
user	0m1.389s
sys	0m0.645s
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 50 > /dev/null

real	0m2.639s
user	0m1.212s
sys	0m0.628s
$ time ansible all -l 'all:!s46:!s48:!s49:!s50' -m raw -a revisar -f 50 > /dev/null

real	0m2.615s
user	0m1.218s
sys	0m0.573s
$ time ansible-playbook revisar.yml -f 50 -T 3 > /dev/null

real	0m11.019s
user	0m1.014s
sys	0m0.485s
$ time ansible-playbook revisar.yml -f 50 -T 3 > /dev/null

real	0m10.995s
user	0m0.969s
sys	0m0.531s
```
- 46 sanos, 50 a la vez: flota 1,2 s (dos veces) · Ansible -f 50 2,6 s (2,639 y 2,615). 10 a la vez: 5,4 · 5,7 s.
- Ansible -f 5: 12,0 y 10,5 s (la 1.ª corrida más lenta; flota no se midió con 5).
- Los 50 con los 4 malos: flota -p 50 10,2 s · ansible-playbook -f 50 -T 3 11,0 s. Los dos los marca el timeout de 10 s de s49.
