# SALIDA — disco (cultura-devops, tanda evergreen de Linux)

> Corrida del 2026-10-23 12:51 en un contenedor: Ubuntu 24.04.4 LTS, GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu).

```
### 1 · El error
$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M     0   20M   0% /datos

$ dd if=/dev/zero of=backup.tar bs=1M count=30 status=none
dd: error writing 'backup.tar': No space left on device

$ echo "una línea más" >> app.log
/demo.sh: line 5: echo: write error: No space left on device

$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M   20M     0 100% /datos

### 2 · Quién se comió el espacio
$ du -sh /datos/* | sort -h
0	/datos/app.log
0	/datos/cache
0	/datos/logs
20M	/datos/backup.tar

$ du -ah /datos | sort -h | tail -n 3
0	/datos/logs
20M	/datos
20M	/datos/backup.tar

$ find /datos -type f -size +5M -exec ls -lh {} \;
-rw-r--r-- 1 root root 20M Oct 23 17:51 /datos/backup.tar

$ rm backup.tar

$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M     0   20M   0% /datos

### 3 · Borré el fichero y el espacio no vuelve
$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M   15M  5.0M  75% /datos

$ rm app.log

$ ls -lh /datos
total 0
drwxr-xr-x 2 root root 40 Oct 23 17:51 cache
drwxr-xr-x 2 root root 40 Oct 23 17:51 logs

$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M   15M  5.0M  75% /datos

$ lsof +L1 2>/dev/null | grep -E "COMMAND|/datos"
COMMAND PID USER   FD   TYPE DEVICE SIZE/OFF NLINK NODE NAME
sleep    27 root    3w   REG  0,102 15728640     0    3 /datos/app.log (deleted)

$ ls -l /proc/27/fd | grep datos
l-wx------ 1 root root 64 Oct 23 17:51 3 -> /datos/app.log (deleted)

# Si no puedes reiniciar el proceso: vaciar el fichero abierto por su descriptor
$ : > /proc/27/fd/3

$ df -h /datos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            20M     0   20M   0% /datos

### 4 · Hay espacio, pero «No space left on device»
$ df -h /inodos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            50M     0   50M   0% /inodos

$ df -i /inodos
Filesystem     Inodes IUsed IFree IUse% Mounted on
tmpfs             200     1   199    1% /inodos

$ for i in $(seq 1 300); do echo x > "f$i" || { echo "falló en el fichero $i"; break; }; done
/demo.sh: line 5: f200: No space left on device
falló en el fichero 200

$ df -h /inodos
Filesystem      Size  Used Avail Use% Mounted on
tmpfs            50M  796K   50M   2% /inodos

$ df -i /inodos
Filesystem     Inodes IUsed IFree IUse% Mounted on
tmpfs             200   200     0  100% /inodos

$ ls | wc -l
199

```
