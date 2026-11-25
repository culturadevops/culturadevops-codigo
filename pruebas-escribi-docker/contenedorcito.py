#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contenedorcito — un contenedor de verdad, hecho a mano, en Python puro.

Vídeo 223 · «Escribí un Docker en Python: qué es de verdad un contenedor».

⛔ NO hay bibliotecas: `ctypes` habla con libc directamente. Tampoco hay nada compilado. Un
contenedor no es una tecnología: son tres llamadas al sistema que ya existían.

    unshare()      pide namespaces nuevos
    chroot()       cambia cuál es la raíz del sistema de ficheros
    mount()        monta /proc dentro, para que el proceso se vea a sí mismo

⚠️ HACE FALTA CAP_SYS_ADMIN (en Docker, `--privileged`). Y eso NO es un atajo del vídeo: es
exactamente lo que hace el demonio de Docker, y es por lo que corre como root.

Uso:  python contenedorcito.py /rootfs /bin/sh
"""
import ctypes
import os
import sys

libc = ctypes.CDLL("libc.so.6", use_errno=True)

# Las banderas de unshare(2). Los números están en <linux/sched.h> y no cambian nunca.
CLONE_NEWNS = 0x00020000      # sistema de ficheros: puntos de montaje propios
CLONE_NEWUTS = 0x04000000     # hostname propio
CLONE_NEWPID = 0x20000000     # tabla de procesos propia
CLONE_NEWIPC = 0x08000000     # colas de mensajes y memoria compartida
MS_PRIVATE, MS_REC = 1 << 18, 1 << 14


def revienta(que):
    e = ctypes.get_errno()
    sys.exit(f"[X] {que} falló: errno={e} ({os.strerror(e)})")


SILENCIO = os.environ.get("CALLADO") == "1"


def p(*a):
    # Con CALLADO=1 no se narra nada: sirve para las pruebas que solo miden, donde la traza
    # se mezclaba con la salida del programa de dentro y no habia forma de leer el resultado.
    if SILENCIO:
        return
    # ⛔ flush obligatorio. El hijo termina con os._exit(), que NO vacía el búfer: sin esto el
    #    contenedor hacía su trabajo entero y por pantalla no salía absolutamente nada.
    print(*a, flush=True)


def main():
    raiz = sys.argv[1] if len(sys.argv) > 1 else "/rootfs"
    orden = sys.argv[2:] or ["/bin/sh"]

    # ── 1 · PEDIR LOS NAMESPACES ────────────────────────────────────────────
    # ⚠️ EL DETALLE QUE CONFUNDE A TODO EL MUNDO, y que se ve en la corrida:
    #    UTS, MNT e IPC afectan al proceso QUE LLAMA, aquí y ahora.
    #    PID no: solo los HIJOS que nazcan después entran en la tabla nueva.
    #    Por eso hay que hacer fork justo después, y por eso un contenedor necesita un init.
    if libc.unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWIPC) != 0:
        revienta("unshare")
    p("1. unshare UTS+PID+MNT+IPC ... OK")

    nombre = b"contenedorcito"
    if libc.sethostname(nombre, len(nombre)) != 0:
        revienta("sethostname")
    p("2. sethostname ... OK  (y ojo: esto ya cambió el hostname del PADRE)")

    # Los montajes que hagamos dentro no deben propagarse al sistema de fuera.
    if libc.mount(b"none", b"/", None, MS_REC | MS_PRIVATE, None) != 0:
        revienta("mount privado de /")

    pid = os.fork()
    if pid == 0:
        # ── 2 · DENTRO DEL CONTENEDOR ───────────────────────────────────────
        p("3. el hijo se ve como PID", os.getpid(), " <- es 1: tabla de procesos propia")

        os.chroot(raiz)
        os.chdir("/")
        p("4. chroot a", raiz, "... OK")
        p("5. hostname que ve el de dentro:", os.uname().nodename)

        # Sin /proc montado, `ps` no ve nada: lee de ahí, no del núcleo directamente.
        os.makedirs("/proc", exist_ok=True)
        if libc.mount(b"proc", b"/proc", b"proc", 0, None) != 0:
            revienta("mount de /proc")
        p("6. mount de /proc ... OK")
        p("7. ejecuto", orden[0], "dentro")
        sys.stdout.flush()
        try:
            os.execv(orden[0], orden)
        except FileNotFoundError:
            # ⚠️ ENOENT AQUÍ NO SIGNIFICA QUE FALTE EL BINARIO. El binario está: lo que falta
            #    es su CARGADOR dinámico. Un ejecutable enlazado dinámicamente arranca pidiendo
            #    /lib/ld-linux..., y dentro del chroot eso no existe. Pasó en la primera corrida.
            p(f"[X] ENOENT ejecutando {orden[0]}.")
            p("    El binario ESTÁ ahí. Lo que falta es su cargador dinámico:")
            p("    dentro del chroot no hay /lib/ld-musl ni /lib64/ld-linux.")
            os._exit(2)
        os._exit(0)

    _, estado = os.waitpid(pid, 0)
    p("8. el contenedor terminó con código", os.waitstatus_to_exitcode(estado))
    p("9. y aquí fuera el hostname es:", os.uname().nodename,
      " <- cambiado, porque UTS SÍ afectó al padre")


if __name__ == "__main__":
    main()
