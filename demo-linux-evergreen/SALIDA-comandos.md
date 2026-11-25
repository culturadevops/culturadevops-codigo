# SALIDA — comandos (cultura-devops, tanda evergreen de Linux)

> Corrida del 2026-10-23 12:51 en un contenedor: Ubuntu 24.04.4 LTS, GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu).

```
### Dónde estoy y quién soy
$ pwd
/home/ana/lab

$ whoami
ana

$ uname -sr
Linux 6.18.33.2-microsoft-standard-WSL2

### Crear carpetas y ficheros
$ mkdir -p proyecto/logs

$ touch proyecto/notas.txt

$ printf "GET /\nGET /login\nPOST /login\nGET /\nGET /admin\nGET /\n" > proyecto/logs/acceso.log

$ echo "hola desde la terminal" > proyecto/notas.txt

$ ls
proyecto

$ ls -l proyecto
total 8
drwxr-xr-x 2 ana ana 4096 Oct 23 17:51 logs
-rw-r--r-- 1 ana ana   23 Oct 23 17:51 notas.txt

$ cd proyecto && pwd && cd ..
/home/ana/lab/proyecto

### Leer
$ cat proyecto/notas.txt
hola desde la terminal

$ head -n 2 proyecto/logs/acceso.log
GET /
GET /login

$ tail -n 2 proyecto/logs/acceso.log
GET /admin
GET /

$ wc -l proyecto/logs/acceso.log
6 proyecto/logs/acceso.log

### Buscar
$ grep -n login proyecto/logs/acceso.log
2:GET /login
3:POST /login

$ grep -c "GET /$" proyecto/logs/acceso.log
3

$ find . -name "*.log"
./proyecto/logs/acceso.log

$ sort proyecto/logs/acceso.log | uniq -c | sort -rn
      3 GET /
      1 POST /login
      1 GET /login
      1 GET /admin

### Copiar, mover, borrar
$ cp proyecto/notas.txt proyecto/notas.bak

$ mv proyecto/notas.bak proyecto/copia.txt

$ ls proyecto
copia.txt
logs
notas.txt

$ rm proyecto/copia.txt

$ ls proyecto
logs
notas.txt

### Permisos
$ printf "#!/bin/bash\necho funciona\n" > hola.sh

$ ./hola.sh
/demo.sh: line 5: ./hola.sh: Permission denied

$ chmod +x hola.sh

$ ls -l hola.sh | cut -d" " -f1,9
-rwxr-xr-x hola.sh

$ ./hola.sh
funciona

### Comprimir
$ tar -czf proyecto.tar.gz proyecto

$ tar -tzf proyecto.tar.gz
proyecto/
proyecto/notas.txt
proyecto/logs/
proyecto/logs/acceso.log

### Procesos
$ ps -o pid,cmd -p 45
    PID CMD
     45 sleep 300

$ kill 45

$ ps -p 45 || echo 'ya no existe'
    PID TTY          TIME CMD
ya no existe

### Disco y memoria
$ df -h / | sed "s/overlay */overlay /"
Filesystem      Size  Used Avail Use% Mounted on
overlay 1007G  284G  672G  30% /

$ du -sh proyecto
16K	proyecto

$ free -h | head -2
               total        used        free      shared  buff/cache   available
Mem:            15Gi       3.7Gi       2.9Gi        25Mi       9.0Gi        11Gi

### Ayuda
$ which tar
/usr/bin/tar

$ ls --help | head -n 3
Usage: ls [OPTION]... [FILE]...
List information about the FILEs (the current directory by default).
Sort entries alphabetically if none of -cftuvSUX nor --sort is specified.

```
