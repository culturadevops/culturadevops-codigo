# Salida ejecutada — vídeo 223 «Escribí un Docker en Python»

> Corrida del 2026-09-08 en `python:3.12-slim --privileged`. `contenedorcito.py` son ~90 líneas de
> Python sin una sola dependencia: `ctypes` habla con libc directamente. Nada compilado.
> Reproducible con `bash demo.sh` dentro de un contenedor privilegiado.

---

## 1 · Una imagen es un tar. No hay magia.

```
   ficheros en el rootfs: 87
   tamaño en disco:       8.7M
   primer nivel: bin dev etc home lib media mnt opt proc root run
                 sbin srv sys tmp usr var
```

Se obtiene con `docker export`, que es literalmente sacar el sistema de ficheros a un tar.

**Y el detalle que sorprende, comprobado aparte:**

```
   ficheros regulares:                    87
   enlaces simbólicos:                   335
   enlaces en /bin que van a busybox:     81
   tamaño de busybox:                804.616 bytes
```

Un sistema operativo entero en 87 ficheros de verdad, porque 81 de las órdenes de `/bin` son
enlaces al **mismo** binario de 800 KB. `ls`, `cat`, `ps` y `sh` son el mismo programa mirando con
qué nombre lo llamaste.

## 2 · 🥇 EL ENOENT QUE NO ES UN FICHERO QUE FALTA

```
   ¿está el binario dentro del chroot vacío?  SÍ, ahí está, 158632 bytes

   7. ejecuto /bin/ls dentro
   [X] ENOENT ejecutando /bin/ls.
       El binario ESTÁ ahí. Lo que falta es su cargador dinámico.

   y lo que le falta de verdad:
     linux-vdso.so.1
     libselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1
```

**«No such file or directory» sobre un fichero que está delante de ti.** El binario existe y pesa
158 KB; lo que no existe dentro del chroot es el cargador dinámico que ese binario pide al
arrancar. El núcleo devuelve ENOENT y no dice cuál de los dos ficheros falta.

🔗 Es exactamente el mismo asunto que «Tu binario de Go no es tan estático como crees»
(golandia 161), visto desde el otro lado.

## 3 · 🥇 Y AHORA EL CONTENEDOR, FUNCIONANDO

```
   1. unshare UTS+PID+MNT+IPC ... OK
   2. sethostname ... OK  (y ojo: esto ya cambió el hostname del PADRE)
   3. el hijo se ve como PID 1  <- tabla de procesos propia
   4. chroot a /rootfs ... OK
   5. hostname que ve el de dentro: contenedorcito
   6. mount de /proc ... OK

   --- ya estoy dentro ---
   me veo como PID: 1
   hostname:        contenedorcito
   procesos que veo desde dentro:
   PID   COMMAND
       1 busybox
       3 ps
       4 head
   raiz: bin dev etc home lib media mnt opt proc root run sbin srv sys tmp usr var
```

Tres procesos en total. Otro hostname. Otra raíz. Y ni una biblioteca de terceros.

⚠️ **Fíjate en el paso 2 y en el 9**: el hostname del proceso PADRE también cambió. UTS, MNT e IPC
afectan a quien llama a `unshare`; PID **no**, solo a los hijos que nazcan después. Por eso hay
que hacer `fork` justo detrás, y por eso un contenedor necesita un proceso init.

## 4 · 🥇 EL AISLAMIENTO ES DE VERDAD

El de fuera arranca un proceso; el de dentro intenta verlo y matarlo:

```
   el de FUERA arranca un proceso con PID 40.
   ¿lo VE el de dentro?     NO
   ¿puede MATARLO?          NO: para él, ese PID no existe
   ¿sigue vivo el de fuera? SÍ
```

## 5 · ⚖️ Y LO QUE **NO** AÍSLA (la mitad honesta)

```
   núcleo que ve el de FUERA:   6.18.33.2-microsoft-standard-WSL2
   núcleo que ve el de DENTRO:  6.18.33.2-microsoft-standard-WSL2

   memoria que cree tener el de FUERA:   MemTotal: 16101044 kB
   memoria que cree tener el de DENTRO:  MemTotal: 16101044 kB

   usuario que soy dentro: 0
```

- **El mismo núcleo.** No hay máquina virtual. Un fallo del núcleo se lleva por delante a todos
  los contenedores de la máquina a la vez.
- **La memoria de la máquina entera.** Los namespaces separan lo que se *ve*; no limitan lo que se
  *gasta*. Eso son los cgroups, y son otra cosa que no está en este programa.
- **Soy root.** Sin namespace de usuario, el root de dentro es el root de fuera.

---

## ⛔ Lo que NO hace, dicho entero

- No construye imágenes ni las descarga: la de aquí se saca con `docker export`.
- No hay sistema de ficheros por capas.
- No hay red propia: eso son veth y netlink, y es otro vídeo.
- No hay cgroups, así que no hay límites de memoria ni de CPU.
- Necesita `--privileged` (CAP_SYS_ADMIN), que es justo lo que necesita el demonio de Docker.

## Tropiezos reales de la construcción (van en el guion)

1. `os._exit()` **no vacía el búfer de stdout**: el hijo hacía su trabajo entero y por pantalla no
   salía nada. Se perdió una corrida completa buscando un fallo que no existía.
2. Un contenedor de Docker no puede llamarse `_alp`: los nombres no pueden empezar por guion bajo.
3. Con la traza del contenedorcito activada, la salida del programa de dentro y la de fuera se
   mezclaban hasta ser ilegibles. De ahí la variable `CALLADO=1`.
