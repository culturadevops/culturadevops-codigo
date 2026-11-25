# Contenedores por dentro: qué son de verdad (curso completo en un vídeo) — lo que sale en pantalla

Comandos y salidas **tal y como salen en las terminales del vídeo**, en el mismo orden.
Se sacaron automáticamente del guion del vídeo; no se escribió nada de memoria.
Las líneas con `$` son lo que tecleas; el resto es la salida que se midió al grabarlo
(tus hashes, tiempos e IDs van a ser otros).

## 1. en mi máquina

```console
$ docker run --rm alpine id

uid=0(root) gid=0(root)
```

## 2. en mi máquina

```console
$ mount -t tmpfs none /tmp/m

mount: permission denied (are you root?)
```

## 3. en mi máquina · dentro del contenedor

```console
$ ls -l /proc/self/ns/

cgroup -> cgroup:[4026532465]
ipc    -> ipc:[4026532463]
mnt    -> mnt:[4026532461]
net    -> net:[4026532466]
pid    -> pid:[4026532464]
user   -> user:[4026531837]
uts    -> uts:[4026532462]
```

## 4. en mi máquina · los del anfitrión

```console
cgroup -> cgroup:[4026531835]
ipc    -> ipc:[4026532210]
mnt    -> mnt:[4026532301]
net    -> net:[4026532233]
pid    -> pid:[4026532302]
user   -> user:[4026531837]
uts    -> uts:[4026532222]
```

## 5. en mi máquina · dentro del contenedor

```console
$ mount | grep ' / '

overlay on / type overlay (rw,
  lowerdir=/var/lib/.../snapshots/4127/fs
  upperdir=/var/lib/.../snapshots/4131/fs
  workdir=/var/lib/.../snapshots/4131/work)
```

## 6. en mi máquina · docker run -m 64m

```console
free dice        15724 MB
el cgroup dice      64 MB
nproc dice          24 procesadores
```

## 7. dónde está el número de verdad

```console
$ cat /sys/fs/cgroup/memory.max
67108864

# 64 MB. Este es el que manda.
```

## 8. en mi máquina · las que NO tienes

```console
!cap_sys_admin      administrar el sistema
!cap_sys_module     cargar módulos del núcleo
!cap_sys_ptrace     espiar otros procesos
!cap_net_admin      tocar la red del anfitrión
!cap_sys_time       cambiar la hora
!cap_syslog         leer el registro del núcleo
```

## 9. en mi máquina · siendo root

```console
$ date -s '2020-01-01'

date: can't set date: Operation not permitted
```

## 10. en mi máquina · docker

```console
$ cat /proc/self/uid_map

         0          0  4294967295

# dentro 0  ->  fuera 0
# y abarca TODOS los usuarios
```

## 11. en mi máquina · podman sin root

```console
$ cat /proc/self/uid_map

         0       1000          1
         1     524288      65536

# dentro 0  ->  fuera 1000
```

## 12. en mi máquina · dentro del contenedor

```console
$ ip -4 addr
lo    127.0.0.1/8
eth0  172.17.0.2/16

$ ip route
default via 172.17.0.1 dev eth0
```

## 13. en mi máquina

```console
$ touch /datos/creado-por-root && ls -l /datos

-rw-r--r--  1 root  root  0  creado-por-root
```

## 14. en mi máquina · docker run -u 1000:1000

```console
$ id -u
1000

$ touch /datos/creado-por-1000
touch: /datos/creado-por-1000: Permission denied
```

## 15. en mi máquina · lo que tarda docker stop

```console
sleep como PID 1 (directo)     10299 ms
envuelto en un shell             126 ms
```

## 16. en mi máquina · la comprobación

```console
siendo PID 1, me mando SIGTERM a mí mismo:
  -> sigo vivo

el mismo proceso, siendo un hijo normal:
  -> murió con SIGTERM
```
